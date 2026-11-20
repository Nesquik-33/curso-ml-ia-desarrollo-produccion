"""Utilidades comunes del pico: rutas, registro a pantalla y fichero, preprocesado de imagen (el MISMO en entrenamiento y en la API),
bootstrap y limitacion a 2 nucleos (como un Codespace). Sin rutas personales: todo cuelga de la carpeta del pico."""
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
TRABAJO = AQUI / '_trabajo'          # regenerable: datos descargados, modelos, base de MLflow
SALIDAS = AQUI / 'salidas'
CLASES = ['gato', 'perro']           # indice 0 = gato, 1 = perro
SEMILLA = 42


class Tee:
    def __init__(self, ruta):
        self.f = open(ruta, 'w', encoding='utf-8')

    def write(self, s):
        sys.__stdout__.write(s)
        self.f.write(s)

    def flush(self):
        sys.__stdout__.flush()
        self.f.flush()


def iniciar_salida(etapa):
    SALIDAS.mkdir(exist_ok=True)
    TRABAJO.mkdir(exist_ok=True)
    marca = time.strftime('%Y%m%d_%H%M%S')
    sys.stdout = Tee(SALIDAS / f'salida_{etapa}_{marca}.txt')


def guardar_json(nombre, obj):
    SALIDAS.mkdir(exist_ok=True)
    (SALIDAS / nombre).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


def cargar_json(nombre):
    return json.loads((SALIDAS / nombre).read_text(encoding='utf-8'))


def limitar_a_dos_nucleos():
    """Aproxima un Codespace de 2 nucleos: afinidad del proceso a 2 procesadores logicos + 2 hilos en torch/onnxruntime.
    En Windows los logicos 0 y 1 pueden ser dos hilos del mismo nucleo fisico: el tiempo es una referencia, no una garantia."""
    if os.name == 'nt':
        import ctypes
        k = ctypes.windll.kernel32
        k.SetProcessAffinityMask(k.GetCurrentProcess(), ctypes.c_size_t(0b11))
    elif hasattr(os, 'sched_setaffinity'):
        os.sched_setaffinity(0, {0, 1})
    os.environ['OMP_NUM_THREADS'] = '2'
    os.environ['MKL_NUM_THREADS'] = '2'


def preparar_imagen(img, lado):
    """Imagen PIL cualquiera -> arreglo uint8 (lado, lado, 3). Unico sitio donde se decide el preprocesado.
    Orientacion EXIF, RGB (RGBA/paleta/gris sobre blanco), recorte centrado a cuadrado y reduccion con LANCZOS (con antialias)."""
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


def png_bytes(arr):
    from PIL import Image
    b = io.BytesIO()
    Image.fromarray(arr).save(b, format='PNG')
    return b.getvalue()


def bootstrap_exactitud(y, pred, n=2000, semilla=SEMILLA):
    """Exactitud y su intervalo del 95 % (percentiles) por bootstrap sobre las filas del test."""
    y, pred = np.asarray(y), np.asarray(pred)
    ok = (y == pred).astype(float)
    rng = np.random.default_rng(semilla)
    idx = rng.integers(0, len(ok), size=(n, len(ok)))
    medias = ok[idx].mean(axis=1)
    lo, hi = np.percentile(medias, [2.5, 97.5])
    return {'exactitud': round(float(ok.mean()), 4), 'ic95': [round(float(lo), 4), round(float(hi), 4)], 'n_test': int(len(ok))}


def cpu_info():
    import platform
    return {'sistema': platform.platform(), 'procesador': platform.processor(), 'nucleos_logicos_visibles': os.cpu_count()}
