"""Laboratorio S3: ¿perro o gato? con una red neuronal preentrenada (transferencia).

MobileNetV3-small preentrenada en ImageNet, CONGELADA, convierte cada foto de 128×128 en 576 números (rasgos).
Encima se entrena solo una regresión logística (la «cabeza»). Todo en CPU, semilla 42.

Datos: Oxford-IIIT Pet (Parkhi, Vedaldi, Zisserman, Jawahar, «Cats and Dogs», CVPR 2012), licencia CC BY-SA 4.0
(https://www.robots.ox.ac.uk/~vgg/data/pets/). Los derechos de cada foto siguen en sus autores.
En el nombre de fichero, la inicial MAYÚSCULA es gato y la minúscula es perro.

Uso (desde 04-Proyecto-Base, para que se importe ia_mlops y se use la base MLflow del proyecto):
    python RUTA/red_gato_perro.py datos [--por-clase 300]
    python RUTA/red_gato_perro.py entrenar
    python RUTA/red_gato_perro.py predecir RUTA_FOTO
"""
import argparse
import csv
import io
import os
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

import numpy as np

SEMILLA = 42
LADO = 128
CLASES = ['gato', 'perro']                     # índice 0 = gato, 1 = perro
PETS_URL = 'https://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz'
CARPETA = Path(os.environ.get('DATOS_MASCOTAS', Path.home() / 'datos-mascotas'))   # la variable solo hace falta para cambiarla
TAR = CARPETA / 'images.tar.gz'
FOTOS = CARPETA / 'fotos'
REPARTO = CARPETA / 'reparto.csv'
NOMBRE = 'gato-perro'                          # experimento y modelo registrado en MLflow
IMN_MEDIA, IMN_STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


def preparar_imagen(img, lado=LADO):
    """Imagen PIL -> arreglo uint8 (lado, lado, 3): orientación EXIF, RGB, recorte centrado a cuadrado y reducción LANCZOS.
    Es el MISMO preprocesado al preparar los datos y al predecir."""
    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(img)
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGBA')
        fondo = Image.new('RGBA', img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(fondo, img)
    img = img.convert('RGB')
    w, h = img.size
    m = min(w, h)
    img = img.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))
    if m != lado:
        img = img.resize((lado, lado), Image.LANCZOS)
    return np.asarray(img, dtype=np.uint8)


# ---------------------------------------------------------------- datos
def descargar():
    if TAR.exists():
        print(f'Ya descargado: {TAR} ({TAR.stat().st_size / 1e6:.1f} MB)')
        return
    CARPETA.mkdir(parents=True, exist_ok=True)
    tmp = TAR.with_suffix('.part')
    print(f'Descargando {PETS_URL} (unos 792 MB) ...')
    t0 = time.perf_counter()
    with urllib.request.urlopen(PETS_URL) as r, open(tmp, 'wb') as f:
        total = int(r.headers.get('Content-Length') or 0)
        hecho, siguiente = 0, 10
        while True:
            bloque = r.read(1 << 20)
            if not bloque:
                break
            f.write(bloque)
            hecho += len(bloque)
            if total and hecho * 100 / total >= siguiente:
                print(f'  {siguiente:3d} %  ({hecho / 1e6:.0f} MB, {time.perf_counter() - t0:.0f} s)')
                siguiente += 10
    tmp.rename(TAR)
    print(f'Descarga completa en {time.perf_counter() - t0:.0f} s')


def es_foto(nombre):
    return nombre.startswith('images/') and nombre.endswith('.jpg')


def orden_datos(por_clase):
    from PIL import Image
    descargar()
    t0 = time.perf_counter()
    # 1.ª pasada: solo los nombres (para elegir con la semilla sin cargar 792 MB en memoria)
    with tarfile.open(TAR, 'r|gz') as t:
        nombres = sorted(m.name for m in t if m.isfile() and es_foto(m.name))
    rng = np.random.default_rng(SEMILLA)
    candidatos = {}
    for c, clase in enumerate(CLASES):
        lista = [n for n in nombres if (n.split('/')[-1][0].isupper()) == (c == 0)]
        rng.shuffle(lista)
        candidatos[clase] = lista[:por_clase + 30]          # unos pocos de reserva por si alguna foto no se puede abrir
    n_gatos = sum(n.split('/')[-1][0].isupper() for n in nombres)
    print(f'En el archivo: {n_gatos} fotos de gato y {len(nombres) - n_gatos} de perro. Se usan {por_clase} de cada clase.')
    buscados = {n: clase for clase, lista in candidatos.items() for n in lista}
    # 2.ª pasada: abrir solo las elegidas
    leidas = {}
    with tarfile.open(TAR, 'r|gz') as t:
        for m in t:
            if m.name in buscados:
                try:
                    img = Image.open(io.BytesIO(t.extractfile(m).read()))
                    img.load()
                    leidas[m.name] = preparar_imagen(img)
                except Exception:
                    pass
    filas = []
    for clase in CLASES:
        destino = FOTOS / clase
        destino.mkdir(parents=True, exist_ok=True)
        for viejo in destino.glob('*.png'):
            viejo.unlink()
        validas = [n for n in candidatos[clase] if n in leidas][:por_clase]
        if len(validas) < por_clase:
            sys.exit(f'Solo hay {len(validas)} fotos válidas de {clase}')
        idx = np.arange(len(validas))
        rng.shuffle(idx)
        n_tr, n_va = int(round(0.70 * len(idx))), int(round(0.15 * len(idx)))
        for pos, i in enumerate(idx):
            parte = 'train' if pos < n_tr else ('val' if pos < n_tr + n_va else 'test')
            archivo = Path(validas[i]).stem + '.png'
            Image.fromarray(leidas[validas[i]]).save(destino / archivo)
            filas.append({'archivo': f'{clase}/{archivo}', 'clase': clase, 'parte': parte})
    with open(REPARTO, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['archivo', 'clase', 'parte'])
        w.writeheader()
        w.writerows(filas)
    print(f'Fotos de {LADO}×{LADO} guardadas en {FOTOS}  ({time.perf_counter() - t0:.0f} s)')
    print(f'{"parte":<6} {"gato":>5} {"perro":>6}')
    for parte in ('train', 'val', 'test'):
        g = sum(1 for r in filas if r['parte'] == parte and r['clase'] == 'gato')
        p = sum(1 for r in filas if r['parte'] == parte and r['clase'] == 'perro')
        print(f'{parte:<6} {g:>5} {p:>6}')
    print(f'Reparto guardado en {REPARTO}')


# ---------------------------------------------------------------- red
def preparar_entorno_ia_mlops():
    """Para que `from ia_mlops import mlflow_ui` funcione: carpeta actual y 04-Proyecto-Base del repositorio."""
    for p in (Path.cwd(), Path(__file__).resolve().parents[3] / '04-Proyecto-Base'):
        if (p / 'ia_mlops').is_dir() and str(p) not in sys.path:
            sys.path.insert(0, str(p))


def mobilenet_congelada():
    import torch
    from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
    m = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT).eval()
    rasgos = torch.nn.Sequential(m.features, m.avgpool)          # 576 rasgos por foto
    for p in rasgos.parameters():
        p.requires_grad = False                                   # CONGELADA: no se entrena
    return rasgos


def extraer_rasgos(rasgos, x, lote=64):
    """x: uint8 (N, 128, 128, 3) -> float32 (N, 576)."""
    import torch
    media = torch.tensor(IMN_MEDIA).view(1, 3, 1, 1)
    std = torch.tensor(IMN_STD).view(1, 3, 1, 1)
    out = []
    with torch.no_grad():
        for i in range(0, len(x), lote):
            xb = torch.from_numpy(np.ascontiguousarray(x[i:i + lote])).permute(0, 3, 1, 2).float() / 255.0
            out.append(torch.flatten(rasgos((xb - media) / std), 1).numpy())
    return np.concatenate(out)


def cargar_parte(parte):
    from PIL import Image
    if not REPARTO.exists():
        sys.exit('No hay datos: ejecuta antes la suborden «datos».')
    with open(REPARTO, encoding='utf-8') as f:
        filas = [r for r in csv.DictReader(f) if r['parte'] == parte]
    x = np.stack([np.asarray(Image.open(FOTOS / r['archivo']).convert('RGB'), dtype=np.uint8) for r in filas])
    y = np.array([CLASES.index(r['clase']) for r in filas])
    return x, y


os.environ.setdefault('MLFLOW_DISABLE_AGENT_HINT', '1')
import warnings
warnings.filterwarnings('ignore')                        # avisos de MLflow que no son errores: la salida queda limpia
try:
    import mlflow.pyfunc as _pyfunc
    _Base = _pyfunc.PythonModel
except Exception:                       # sin mlflow instalado (p. ej., al revisar el fichero): la clase sigue existiendo
    _Base = object


class GatoPerro(_Base):
    """Modelo MLflow: MobileNetV3-small congelada + cabeza logística. Entrada uint8 (N,128,128,3); salida (N,2) = P(gato), P(perro)."""

    def load_context(self, context):
        import torch
        from torchvision.models import mobilenet_v3_small
        m = mobilenet_v3_small(weights=None)
        self.rasgos = torch.nn.Sequential(m.features, m.avgpool).eval()
        self.rasgos.load_state_dict(torch.load(context.artifacts['mobilenet'], map_location='cpu'))
        z = np.load(context.artifacts['cabeza'])
        self.w, self.b = z['w'], float(z['b'])

    def predict(self, context, model_input, params=None):
        if isinstance(model_input, dict):                 # con la firma de tensor con nombre, MLflow entrega {'imagen': arreglo}
            model_input = model_input['imagen']
        x = np.asarray(model_input, dtype=np.uint8)
        f = extraer_rasgos(self.rasgos, x)
        p_perro = 1.0 / (1.0 + np.exp(-(f @ self.w + self.b)))
        return np.stack([1.0 - p_perro, p_perro], axis=1).astype(np.float32)


def orden_entrenar():
    import tempfile
    import torch
    import mlflow
    from mlflow.models.signature import ModelSignature
    from mlflow.types.schema import Schema, TensorSpec
    from sklearn.linear_model import LogisticRegression
    preparar_entorno_ia_mlops()
    from ia_mlops import config, mlflow_ui

    torch.manual_seed(SEMILLA)
    t_total = time.perf_counter()
    x_tr, y_tr = cargar_parte('train')
    x_va, y_va = cargar_parte('val')
    x_te, y_te = cargar_parte('test')
    print(f'Fotos: train {len(y_tr)} · val {len(y_va)} · test {len(y_te)}')

    rasgos = mobilenet_congelada()
    n_par = sum(p.numel() for p in rasgos.parameters())
    print(f'MobileNetV3-small cargada y congelada: {n_par:,} parámetros que NO se entrenan'.replace(',', '.'))
    t0 = time.perf_counter()
    f_tr, f_va, f_te = extraer_rasgos(rasgos, x_tr), extraer_rasgos(rasgos, x_va), extraer_rasgos(rasgos, x_te)
    t_rasgos = time.perf_counter() - t0
    print(f'Rasgos extraídos: {f_tr.shape[1]} por foto en {t_rasgos:.1f} s')

    t1 = time.perf_counter()
    from sklearn.metrics import log_loss
    mejor = None
    for c in (0.01, 0.1, 1.0, 10.0):
        m = LogisticRegression(C=c, max_iter=3000).fit(f_tr, y_tr)
        acc = float((m.predict(f_va) == y_va).mean())
        perdida = float(log_loss(y_va, m.predict_proba(f_va)))
        print(f'  C={c:<5}  exactitud en val = {acc:.3f}  pérdida logarítmica en val = {perdida:.3f}')
        if mejor is None or (acc, -perdida) > (mejor[0], -mejor[1]):      # gana la exactitud; si empatan, la menor pérdida
            mejor = (acc, perdida, c, m)
    acc_va, _, c, cabeza = mejor
    t_cabeza = time.perf_counter() - t1
    acc_te = float((cabeza.predict(f_te) == y_te).mean())
    print(f'Cabeza entrenada en {t_cabeza:.1f} s · C elegida = {c}')
    print(f'Exactitud en val = {acc_va:.3f} · en test = {acc_te:.3f}  ({int(round((1 - acc_te) * len(y_te)))} fallos de {len(y_te)})')

    # ---- MLflow: misma base que el proyecto del curso (models/mlflow.db)
    mlflow.set_tracking_uri(mlflow_ui.uri())
    if mlflow.get_experiment_by_name(NOMBRE) is None:
        mlflow.create_experiment(NOMBRE, artifact_location=(config.MODELOS / 'mlartifacts').resolve().as_uri())
    mlflow.set_experiment(NOMBRE)
    firma = ModelSignature(inputs=Schema([TensorSpec(np.dtype(np.uint8), (-1, LADO, LADO, 3), 'imagen')]),
                           outputs=Schema([TensorSpec(np.dtype(np.float32), (-1, 2), 'probabilidades')]))
    with tempfile.TemporaryDirectory() as tmp, mlflow.start_run(run_name='mobilenet-congelada+logistica'):
        ruta_mb, ruta_cab = Path(tmp) / 'mobilenet_rasgos.pt', Path(tmp) / 'cabeza.npz'
        torch.save(rasgos.state_dict(), ruta_mb)
        np.savez(ruta_cab, w=cabeza.coef_[0].astype(np.float32), b=np.float32(cabeza.intercept_[0]))
        mlflow.log_params({'red_base': 'mobilenet_v3_small (ImageNet, congelada)', 'rasgos': f_tr.shape[1], 'lado': LADO,
                           'cabeza': 'LogisticRegression', 'C': c, 'n_train': len(y_tr), 'n_val': len(y_va), 'n_test': len(y_te),
                           'semilla': SEMILLA, 'datos': 'Oxford-IIIT Pet (CC BY-SA 4.0)'})
        mlflow.log_metrics({'exactitud_val': acc_va, 'exactitud_test': acc_te,
                            'segundos_rasgos': t_rasgos, 'segundos_cabeza': t_cabeza})
        import torchvision
        info = mlflow.pyfunc.log_model(
            name='modelo', python_model=GatoPerro(), signature=firma,
            artifacts={'mobilenet': str(ruta_mb), 'cabeza': str(ruta_cab)},
            pip_requirements=[f'mlflow=={mlflow.__version__}', f'torch=={torch.__version__.split("+")[0]}',
                              f'torchvision=={torchvision.__version__.split("+")[0]}', 'numpy', 'pillow'],
            registered_model_name=NOMBRE)
        version = info.registered_model_version
    print(f'Tiempo total (con registrar en MLflow): {time.perf_counter() - t_total:.1f} s')
    print(f'Registrado en MLflow como «{NOMBRE}», versión {version}')


def orden_predecir(ruta_foto):
    import mlflow
    from PIL import Image
    preparar_entorno_ia_mlops()
    from ia_mlops import mlflow_ui
    mlflow.set_tracking_uri(mlflow_ui.uri())
    versiones = mlflow.MlflowClient().search_model_versions(f"name='{NOMBRE}'")
    if not versiones:
        sys.exit(f'No hay ningún modelo «{NOMBRE}» registrado: ejecuta antes la suborden «entrenar».')
    v = max(int(m.version) for m in versiones)
    modelo = mlflow.pyfunc.load_model(f'models:/{NOMBRE}/{v}')
    x = preparar_imagen(Image.open(ruta_foto))[None]
    p = modelo.predict(x)[0]
    print(f'Modelo «{NOMBRE}» versión {v} · foto {Path(ruta_foto).name}')
    print(f'gato {p[0]:.2f} / perro {p[1]:.2f}'.replace('.', ','))
    print(f'Predicción: {CLASES[int(np.argmax(p))]}')


def main(argv=None):
    try:
        sys.stdout.reconfigure(line_buffering=True)          # el progreso se ve al momento aunque la salida vaya a un fichero
    except Exception:
        pass
    ap =argparse.ArgumentParser(description='¿Perro o gato? Transferencia con MobileNetV3-small congelada.')
    sub = ap.add_subparsers(dest='orden', required=True)
    d = sub.add_parser('datos', help='descarga Oxford-IIIT Pet y prepara fotos 128×128 equilibradas')
    d.add_argument('--por-clase', type=int, default=300)
    sub.add_parser('entrenar', help='rasgos de MobileNet + regresión logística; registra en MLflow')
    p = sub.add_parser('predecir', help='predice una foto con la última versión registrada')
    p.add_argument('ruta_foto')
    a = ap.parse_args(argv)
    if a.orden == 'datos':
        orden_datos(a.por_clase)
    elif a.orden == 'entrenar':
        orden_entrenar()
    else:
        orden_predecir(a.ruta_foto)


if __name__ == '__main__':
    main()
