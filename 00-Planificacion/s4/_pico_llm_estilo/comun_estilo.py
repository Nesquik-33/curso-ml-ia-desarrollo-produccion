"""Funciones comunes del pico «LLM de visión que lee el estilo de color».

Todo lo que comparten los cuatro notebooks está aquí para que los notebooks
tengan pocas celdas de código y se lean como una explicación.

Rutas: nada de rutas fijas de Windows. La carpeta de trabajo sale de la
variable de entorno ESTILO_TRABAJO (por defecto ``_trabajo`` junto a este
archivo, ignorada por git) y la caché de Hugging Face de HF_HOME (por defecto
``<trabajo>/hf``).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

import warnings

import numpy as np
from PIL import Image

# Salidas limpias en los notebooks: sin barras de progreso ni avisos que
# imprimen rutas locales de la instalación.
warnings.filterwarnings("ignore", message="IProgress not found")
# Reinhard puede pedir colores fuera de sRGB; se recortan (es lo esperado).
warnings.filterwarnings("ignore", message="Conversion from CIE-LAB")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

# ---------------------------------------------------------------------------
# Rutas y entorno
# ---------------------------------------------------------------------------
AQUI = Path(__file__).resolve().parent


def carpeta_trabajo(valor: str | None = None) -> Path:
    """Carpeta donde cada notebook lee su entrada y deja su salida."""
    ruta = Path(valor or os.environ.get("ESTILO_TRABAJO") or (AQUI / "_trabajo"))
    ruta.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(ruta / "hf"))
    # Pesos de torchvision junto a la caché de Hugging Face (fuera de los artefactos).
    os.environ.setdefault("TORCH_HOME", str(Path(os.environ["HF_HOME"]) / "torch"))
    return ruta


def limitar_hilos(n: int | None = None) -> int:
    """Fija los hilos de PyTorch (variable ESTILO_HILOS o todos los núcleos)."""
    import torch

    n = int(n or os.environ.get("ESTILO_HILOS") or os.cpu_count() or 1)
    torch.set_num_threads(n)
    return n


def mostrar_ruta(ruta: Path, base: Path) -> str:
    """Ruta relativa a la carpeta de trabajo, para no imprimir rutas personales."""
    try:
        return "<trabajo>/" + Path(ruta).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return Path(ruta).name


# ---------------------------------------------------------------------------
# Los cinco ajustes de color (definición exacta)
# ---------------------------------------------------------------------------
# Cada ajuste tiene un rango de muestreo y un valor «neutro» (no cambia nada).
AJUSTES = {
    #  nombre        (mínimo, máximo, neutro)
    "exposicion": (-0.7, 0.7, 0.0),   # pasos de diafragma: multiplica por 2**e
    "temperatura": (-1.0, 1.0, 0.0),  # >0 más cálida (más rojo, menos azul)
    "tinte": (-1.0, 1.0, 0.0),        # >0 más magenta (menos verde), <0 más verde
    "contraste": (0.6, 1.5, 1.0),     # factor alrededor del gris medio 0.5
    "saturacion": (0.2, 1.8, 1.0),    # 0 = blanco y negro, 1 = igual
}
NOMBRES = list(AJUSTES)
NEUTRO = {k: v[2] for k, v in AJUSTES.items()}


def aplicar_ajustes(img: Image.Image, p: dict) -> Image.Image:
    """Aplica los cinco ajustes, en este orden, sobre RGB en [0, 1].

    1. exposición:   x = x * 2**e
    2. temperatura:  R = R * (1 + 0.25 t);  B = B * (1 - 0.25 t)
    3. tinte:        G = G * (1 - 0.20 g)
    4. contraste:    x = (x - 0.5) * c + 0.5
    5. saturación:   Y = 0.299 R + 0.587 G + 0.114 B;  x = Y + (x - Y) * s
    y al final se recorta a [0, 1].
    """
    x = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    x = x * (2.0 ** p["exposicion"])
    x[..., 0] *= 1 + 0.25 * p["temperatura"]
    x[..., 2] *= 1 - 0.25 * p["temperatura"]
    x[..., 1] *= 1 - 0.20 * p["tinte"]
    x = (x - 0.5) * p["contraste"] + 0.5
    y = (0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2])[..., None]
    x = y + (x - y) * p["saturacion"]
    x = np.clip(x, 0.0, 1.0)
    return Image.fromarray((x * 255.0 + 0.5).astype(np.uint8))


def muestrear_ajustes(rng: np.random.Generator) -> dict:
    """Ajustes aleatorios uniformes dentro de cada rango, redondeados a 2 decimales."""
    return {k: round(float(rng.uniform(lo, hi)), 2) for k, (lo, hi, _) in AJUSTES.items()}


def a_json(p: dict) -> str:
    """Texto JSON compacto que el VLM tiene que aprender a escribir."""
    return json.dumps({k: round(float(p[k]), 2) for k in NOMBRES}, ensure_ascii=False)


def recortar_a_rango(p: dict) -> dict:
    return {k: float(np.clip(p[k], AJUSTES[k][0], AJUSTES[k][1])) for k in NOMBRES}


# ---------------------------------------------------------------------------
# Fotos de Oxford-IIIT Pet (CC BY-SA 4.0, Parkhi et al., CVPR 2012)
# ---------------------------------------------------------------------------
URL_PETS = "https://thor.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz"


def _recorte_cuadrado(img: Image.Image, lado: int) -> Image.Image:
    w, h = img.size
    m = min(w, h)
    img = img.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))
    return img.resize((lado, lado), Image.BICUBIC)


def preparar_fotos(trabajo: Path, n_fotos: int, resolucion: int, tar: str | None = None) -> list[Path]:
    """Extrae ``n_fotos`` fotos (mitad gatos, mitad perros) a ``trabajo/fotos_<res>``.

    Lee el images.tar.gz original (variable ESTILO_TAR) o, si no está, lo
    descarga de la web oficial. La elección es determinista (hash del nombre).
    En Oxford-IIIT Pet las razas de gato empiezan por mayúscula.
    """
    destino = trabajo / f"fotos_{resolucion}"
    destino.mkdir(parents=True, exist_ok=True)
    hechas = sorted(destino.glob("*.png"))
    if len(hechas) >= n_fotos:
        return hechas[:n_fotos]
    tar = tar or os.environ.get("ESTILO_TAR")
    if not tar or not Path(tar).exists():
        # Fuera de la carpeta de trabajo, para que los ~800 MB no viajen en los artefactos.
        tar = str(Path(tempfile.gettempdir()) / "oxford_pets_images.tar.gz")
        if not Path(tar).exists():
            print("Descargando Oxford-IIIT Pet (~800 MB)...")
            t0 = time.perf_counter()
            urllib.request.urlretrieve(URL_PETS, tar)
            print(f"Descarga: {time.perf_counter() - t0:.0f} s")
    elegidas = {"gato": [], "perro": []}
    prob = min(1.0, 1.6 * n_fotos / 7390)  # ~7390 fotos en el archivo
    with tarfile.open(tar, "r|gz") as t:
        for m in t:
            nombre = Path(m.name).name
            if not (m.isfile() and nombre.endswith(".jpg")):
                continue
            h = int(hashlib.md5(nombre.encode()).hexdigest(), 16)
            if (h % 10000) / 10000 >= prob:
                continue
            try:
                img = Image.open(io.BytesIO(t.extractfile(m).read()))
                if img.mode != "RGB":  # descartamos grises, CMYK y RGBA raras
                    continue
                img.load()
            except Exception:
                continue
            clase = "gato" if nombre[0].isupper() else "perro"
            elegidas[clase].append((h, nombre, _recorte_cuadrado(img, resolucion)))
    por_clase = n_fotos // 2
    for clase, lista in elegidas.items():
        for _, nombre, img in sorted(lista)[:por_clase]:
            img.save(destino / f"{clase}_{Path(nombre).stem}.png")
    return sorted(destino.glob("*.png"))[:n_fotos]


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------
def _lab(img: Image.Image) -> np.ndarray:
    from skimage.color import rgb2lab

    return rgb2lab(np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0)


def delta_e(img1: Image.Image, img2: Image.Image) -> float:
    """ΔE medio CIEDE2000 píxel a píxel (≈1 apenas visible, >10 muy distinto)."""
    from skimage.color import deltaE_ciede2000

    return float(np.mean(deltaE_ciede2000(_lab(img1), _lab(img2))))


def distancia_histogramas(img1: Image.Image, img2: Image.Image, bins: int = 32) -> float:
    """Distancia de Bhattacharyya media de los histogramas L, a y b (0 = iguales, 1 = disjuntos)."""
    a, b = _lab(img1), _lab(img2)
    rangos = [(0, 100), (-100, 100), (-100, 100)]
    d = []
    for c, r in enumerate(rangos):
        h1, _ = np.histogram(a[..., c], bins=bins, range=r)
        h2, _ = np.histogram(b[..., c], bins=bins, range=r)
        h1 = h1 / h1.sum()
        h2 = h2 / h2.sum()
        d.append(np.sqrt(max(0.0, 1.0 - np.sum(np.sqrt(h1 * h2)))))
    return float(np.mean(d))


def ssim_contenido(img: Image.Image, contenido: Image.Image) -> float:
    """SSIM en escala de grises entre el resultado y la foto de contenido (1 = misma estructura)."""
    from skimage.metrics import structural_similarity

    g1 = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    g2 = np.asarray(contenido.convert("L"), dtype=np.float32) / 255.0
    return float(structural_similarity(g1, g2, data_range=1.0))


def error_por_ajuste(pred: list[dict], real: list[dict]) -> dict:
    """Error medio absoluto de cada ajuste y su versión normalizada por el rango."""
    res = {}
    for k in NOMBRES:
        e = np.mean([abs(p[k] - r[k]) for p, r in zip(pred, real)])
        res[f"mae_{k}"] = float(e)
        res[f"maen_{k}"] = float(e / (AJUSTES[k][1] - AJUSTES[k][0]))
    res["mae_normalizado_medio"] = float(np.mean([res[f"maen_{k}"] for k in NOMBRES]))
    return res


def estadisticas_color(img: Image.Image) -> np.ndarray:
    """27 números que resumen el color: Lab (media, desviación, percentiles 5/50/95) y RGB (media, desviación, percentiles 1/99)."""
    x = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    lab, rgb = _lab(img).reshape(-1, 3), x.reshape(-1, 3)
    return np.concatenate([lab.mean(0), lab.std(0), np.percentile(lab, [5, 50, 95], axis=0).ravel(),
                           rgb.mean(0), rgb.std(0), np.percentile(rgb, [1, 99], axis=0).ravel()])


# ---------------------------------------------------------------------------
# Referencia clásica: Reinhard et al. (2001) en Lab
# ---------------------------------------------------------------------------
def reinhard(referencia: Image.Image, contenido: Image.Image) -> Image.Image:
    """Iguala media y desviación de cada canal Lab del contenido a las de la referencia."""
    from skimage.color import lab2rgb

    r, c = _lab(referencia), _lab(contenido)
    salida = (c - c.mean((0, 1))) / (c.std((0, 1)) + 1e-6) * r.std((0, 1)) + r.mean((0, 1))
    rgb = np.clip(lab2rgb(salida), 0, 1)
    return Image.fromarray((rgb * 255 + 0.5).astype(np.uint8))


# ---------------------------------------------------------------------------
# Datos de trabajo
# ---------------------------------------------------------------------------
def leer_parejas(trabajo: Path, parte: str | None = None) -> list[dict]:
    filas = [json.loads(l) for l in (trabajo / "parejas" / "parejas.jsonl").read_text(encoding="utf-8").splitlines() if l]
    return [f for f in filas if parte is None or f["parte"] == parte]


def abrir(trabajo: Path, relativa: str) -> Image.Image:
    return Image.open(trabajo / "parejas" / relativa).convert("RGB")


def parejas_transferencia(test: list[dict]) -> list[tuple[dict, dict]]:
    """Cada foto editada de test hace de referencia; el contenido es la foto original siguiente."""
    return [(test[i], test[(i + 1) % len(test)]) for i in range(len(test))]


# ---------------------------------------------------------------------------
# El LLM de visión (SmolVLM)
# ---------------------------------------------------------------------------
PROMPT = (
    "Look at the colors of this photo. Estimate the color edits that were applied to it "
    "and answer ONLY with a JSON object with these keys: "
    '"exposicion" (exposure in stops, -0.7 to 0.7), '
    '"temperatura" (white balance, -1 cool/blue to 1 warm/orange), '
    '"tinte" (tint, -1 green to 1 magenta), '
    '"contraste" (contrast factor, 0.6 to 1.5, 1 = unchanged), '
    '"saturacion" (saturation factor, 0.2 to 1.8, 1 = unchanged).'
)


def cargar_vlm(modelo: str):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from transformers.utils import logging as tlog

    tlog.disable_progress_bar()
    tlog.set_verbosity_error()
    proc = AutoProcessor.from_pretrained(modelo)
    vlm = AutoModelForImageTextToText.from_pretrained(modelo, dtype=torch.float32)
    vlm.eval()
    return proc, vlm


# Tras el fine-tuning ya no hace falta explicar la tarea: basta una orden corta
# (secuencias más cortas = entrenamiento e inferencia más rápidos).
PROMPT_CORTO = "Color edits as JSON."


def texto_prompt(proc, prompt: str = PROMPT) -> str:
    mensajes = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    return proc.apply_chat_template(mensajes, add_generation_prompt=True)


def entradas(proc, imagenes, textos):
    # Sin trocear la imagen: una sola vista de 512 px = 64 «palabras» de imagen.
    return proc(text=textos, images=[[im] for im in imagenes], return_tensors="pt",
                padding=True, do_image_splitting=False)


def preguntar(proc, vlm, imagen: Image.Image, max_tokens: int = 80, prompt: str = PROMPT,
              inicio: str = "") -> str:
    """Genera la respuesta. ``inicio`` permite «empezar» la respuesta por el modelo
    (p. ej. '{"exposicion":') para forzar el formato sin enseñarle nada."""
    import torch

    inp = entradas(proc, [imagen], [texto_prompt(proc, prompt) + inicio])
    with torch.no_grad():
        out = vlm.generate(**inp, max_new_tokens=max_tokens, do_sample=False)
    return (inicio + proc.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]).strip()


def preparar_ejemplo(proc, vlm, imagen: Image.Image, ajustes: dict) -> dict:
    """Tokeniza (prompt corto + respuesta) y calcula UNA vez los rasgos de imagen.

    Como el codificador de imagen y el conector están congelados, su salida no
    cambia durante el entrenamiento: calcularla una sola vez ahorra más de la
    mitad del tiempo de cada paso.
    """
    import torch

    prefijo = texto_prompt(proc, PROMPT_CORTO)
    completo = prefijo + " " + a_json(ajustes) + "<end_of_utterance>"
    inp = entradas(proc, [imagen], [completo])
    n_prefijo = entradas(proc, [imagen], [prefijo])["input_ids"].shape[1]
    ids = inp["input_ids"][0]
    etiquetas = ids.clone()
    etiquetas[:n_prefijo] = -100  # solo se aprende la respuesta, no el prompt
    with torch.no_grad():
        rasgos = vlm.model.get_image_features(inp["pixel_values"], inp["pixel_attention_mask"],
                                              return_dict=True).pooler_output[0]
    return {"ids": ids, "etiquetas": etiquetas, "rasgos": rasgos}


def lote(ejemplos: list[dict], pad_id: int) -> dict:
    """Junta ejemplos de distinta longitud rellenando por la derecha."""
    import torch
    from transformers.modeling_outputs import BaseModelOutputWithPooling

    n = max(len(e["ids"]) for e in ejemplos)
    ids = torch.full((len(ejemplos), n), pad_id, dtype=torch.long)
    mascara = torch.zeros((len(ejemplos), n), dtype=torch.long)
    etiquetas = torch.full((len(ejemplos), n), -100, dtype=torch.long)
    for i, e in enumerate(ejemplos):
        L = len(e["ids"])
        ids[i, :L], mascara[i, :L], etiquetas[i, :L] = e["ids"], 1, e["etiquetas"]
    rasgos = BaseModelOutputWithPooling(pooler_output=[e["rasgos"] for e in ejemplos])
    return {"input_ids": ids, "attention_mask": mascara, "labels": etiquetas,
            "mm_encoder_outputs": {"image": rasgos}}


_NUM = r"(-?\d+(?:\.\d+)?)"


def parsear(respuesta: str) -> tuple[dict, bool]:
    """Saca los cinco números de la respuesta. Si falta alguno, pone el neutro y marca fallo."""
    p, completo = {}, True
    try:
        trozo = re.search(r"\{.*?\}", respuesta, re.S)
        datos = json.loads(trozo.group(0)) if trozo else {}
    except Exception:
        datos = {}
    for k in NOMBRES:
        v = datos.get(k) if isinstance(datos, dict) else None
        if isinstance(v, str) and re.fullmatch(r"\s*-?\d+(\.\d+)?\s*", v):
            v = float(v)  # aceptamos «"0.7"» (número entre comillas)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            m = re.search(rf'"?{k}"?\s*:\s*"?{_NUM}"?\s*[,}}]', respuesta)
            v = float(m.group(1)) if m else None
        if v is None:
            completo = False
            v = NEUTRO[k]
        p[k] = float(v)
    return recortar_a_rango(p), completo


def guardar_figura(ruta, dpi: int = 55) -> None:
    """Guarda la figura actual de matplotlib como PNG ligero (paleta de 256 colores)."""
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    plt.savefig(buf, dpi=dpi, format="png")
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Image.open(buf).convert("RGB").quantize(256).save(ruta, optimize=True)


# ---------------------------------------------------------------------------
# Acto 3 (notebook 05): del JSON a una explicación en español
# ---------------------------------------------------------------------------
# Intensidad = (valor - neutro) / (media anchura del rango). Si |intensidad| < 0,15
# se ignora; si < 0,5 es «un poco»; si no, «bastante».
UMBRAL_NULO, UMBRAL_BASTANTE = 0.15, 0.5
#            (adjetivo si sube, adjetivo si baja, acción si sube, acción si baja)
FRASES = {
    "exposicion": ("más luminosa", "más oscura", "se sube {i} la exposición", "se baja {i} la exposición"),
    "temperatura": ("más cálida", "más fría", "se sube {i} la temperatura", "se baja {i} la temperatura"),
    "tinte": ("más magenta", "más verdosa", "se lleva el tinte {i} hacia el magenta", "se lleva el tinte {i} hacia el verde"),
    "contraste": ("con más contraste", "con menos contraste", "se sube {i} el contraste", "se baja {i} el contraste"),
    "saturacion": ("más saturada", "menos saturada", "se sube {i} la saturación", "se baja {i} la saturación"),
}
# Patrones para medir automáticamente si una frase menciona cada ajuste y en qué sentido
# (sube, baja, cualquier mención). _NO_CRUZAR impide saltar de una acción a la siguiente.
_NO_CRUZAR = r"(?:(?!\by\b|sube|baja|lleva|,|;|\.)[^\n]){0,25}"
PATRONES = {
    "exposicion": (rf"sube{_NO_CRUZAR}exposici|más luminos|más clar", rf"baja{_NO_CRUZAR}exposici|más oscur", r"exposici|luminos|oscur|\bclar"),
    "temperatura": (rf"sube{_NO_CRUZAR}temperatura|más cálid|más calid", rf"baja{_NO_CRUZAR}temperatura|más frí|más fri", r"temperatura|cálid|calid|frí|\bfria"),
    "tinte": (r"magenta", r"verd", r"tinte|magenta|verd"),
    "contraste": (rf"sube{_NO_CRUZAR}contraste|más contraste", rf"baja{_NO_CRUZAR}contraste|menos contraste", r"contraste"),
    "saturacion": (rf"sube{_NO_CRUZAR}saturaci|más saturad", rf"baja{_NO_CRUZAR}saturaci|menos saturad", r"saturaci|saturad"),
}


def intensidad(k: str, v: float) -> float:
    lo, hi, n = AJUSTES[k]
    return (v - n) / ((hi - lo) / 2)


def ajustes_relevantes(p: dict) -> dict:
    """{ajuste: +1 o -1} para los ajustes que no son casi nulos, en el orden fijo de NOMBRES."""
    return {k: (1 if intensidad(k, p[k]) > 0 else -1) for k in NOMBRES if abs(intensidad(k, p[k])) >= UMBRAL_NULO}


def _unir(trozos: list) -> str:
    return trozos[0] if len(trozos) == 1 else ", ".join(trozos[:-1]) + " y " + trozos[-1]


def entrada_explicacion(p: dict, formato: str = "facil") -> str:
    """Texto de entrada del notebook 05.

    «json»: el JSON tal cual (el modelo tiene que decidir sentido e intensidad).
    «facil»: sentido e intensidad ya precalculados con las mismas reglas; el modelo solo redacta.
    """
    if formato == "json":
        return "Ajustes: " + a_json(p)
    trozos = []
    for k in NOMBRES:
        x = intensidad(k, p[k])
        if abs(x) < UMBRAL_NULO:
            trozos.append(f"{k}: sin cambio")
        else:
            trozos.append(f"{k}: {'sube' if x > 0 else 'baja'} {'un poco' if abs(x) < UMBRAL_BASTANTE else 'bastante'}")
    return "Cambios: " + "; ".join(trozos)


def frase_objetivo(p: dict, clave: str) -> str:
    """Explicación determinista: reglas + una de 3 plantillas elegida por el hash de ``clave``."""
    rel = ajustes_relevantes(p)
    if not rel:
        return "La referencia apenas tiene ajustes de color: se deja la foto como está."
    adjs, acciones = [], []
    for k, s in rel.items():
        i = "un poco" if abs(intensidad(k, p[k])) < UMBRAL_BASTANTE else "bastante"
        adjs.append(FRASES[k][0 if s > 0 else 1])
        acciones.append(FRASES[k][2 if s > 0 else 3].format(i=i))
    plantilla = int(hashlib.md5(clave.encode()).hexdigest(), 16) % 3
    if plantilla == 0:
        return f"La referencia es {_unir(adjs)}: {_unir(acciones)}."
    if plantilla == 1:
        return f"Para copiar este estilo, {_unir(acciones)}."
    return f"Estilo {_unir(adjs)}. Cambios: {_unir(acciones)}."


_ESPANOL = re.compile(r"\b(se|la|el|más|menos|y|foto|referencia)\b", re.I)
_INGLES = re.compile(r"\b(the|is|and|image|photo|increase|decrease|color)\b", re.I)


def evaluar_frase(texto: str, p: dict) -> dict:
    """Métricas automáticas de una explicación frente a los ajustes reales."""
    t = texto.lower()
    rel = ajustes_relevantes(p)
    aciertos, contrario = 0, 0
    for k, s in rel.items():
        sube, baja, _ = PATRONES[k]
        ok = re.search(sube if s > 0 else baja, t) is not None
        aciertos += int(ok)
        contrario += int(not ok and re.search(baja if s > 0 else sube, t) is not None)
    alucinados = [k for k in NOMBRES if k not in rel and re.search(PATRONES[k][2], t)]
    return {"n_relevantes": len(rel), "aciertos": aciertos, "sentido_contrario": contrario, "alucinados": alucinados,
            "espanol_ok": bool(_ESPANOL.search(t)) and not _INGLES.search(t) and 20 <= len(texto) <= 300}


def resumir_frases(evaluaciones: list) -> dict:
    """Agrega evaluar_frase sobre un conjunto de frases."""
    rel = sum(e["n_relevantes"] for e in evaluaciones) or 1
    return {"pct_ajustes_sentido_correcto": 100 * sum(e["aciertos"] for e in evaluaciones) / rel,
            "pct_ajustes_sentido_contrario": 100 * sum(e["sentido_contrario"] for e in evaluaciones) / rel,
            "pct_frases_con_alucinacion": 100 * float(np.mean([bool(e["alucinados"]) for e in evaluaciones])),
            "pct_frases_espanol_longitud_ok": 100 * float(np.mean([e["espanol_ok"] for e in evaluaciones])),
            "pct_frases_perfectas": 100 * float(np.mean([e["aciertos"] == e["n_relevantes"] and not e["alucinados"] for e in evaluaciones]))}


class Cronometro:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.s = time.perf_counter() - self.t0


def memoria_mb() -> float:
    """Memoria residente máxima del proceso (pico) en MB, si psutil lo permite."""
    try:
        import psutil

        info = psutil.Process().memory_info()
        return round(getattr(info, "peak_wset", info.rss) / 2**20, 1)
    except Exception:
        return float("nan")


def tamano_mb(ruta: Path) -> float:
    ruta = Path(ruta)
    archivos = [ruta] if ruta.is_file() else [f for f in ruta.rglob("*") if f.is_file()]
    return round(sum(f.stat().st_size for f in archivos) / 2**20, 2)


def mlflow_local(trabajo: Path):
    """MLflow en una base temporal dentro de la carpeta de trabajo (nunca la del proyecto)."""
    import mlflow

    uri = os.environ.get("ESTILO_MLFLOW") or ("sqlite:///" + (trabajo / "mlflow.db").as_posix())
    mlflow.set_tracking_uri(uri)
    nombre = "pico-llm-estilo"
    if mlflow.get_experiment_by_name(nombre) is None:
        # Los artefactos también dentro de la carpeta de trabajo, no en el repo.
        mlflow.create_experiment(nombre, artifact_location=(trabajo / "mlartifacts").resolve().as_uri())
    mlflow.set_experiment(nombre)
    return mlflow
