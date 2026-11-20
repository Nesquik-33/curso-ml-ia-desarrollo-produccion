"""API de ejemplo con subida de imagen (FastAPI). Carga el modelo en formato MLflow con mlflow.pyfunc (como la API del curso base carga
el suyo con mlflow.sklearn) y usa SU FIRMA para saber el lado de entrada. Defensas: tamano maximo, formato real (no el nombre ni el
Content-Type), pixeles maximos (bombas de descompresion), imagenes truncadas, orientacion EXIF, canales alfa/paleta/gris, y respuesta
sin datos del usuario. No guarda nada en disco."""
import io
import os
import time

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from comun import CLASES, preparar_imagen

MAX_BYTES = int(os.environ.get('MAX_BYTES', 2 * 1024 * 1024))       # 2 MB
MAX_PIXELES = int(os.environ.get('MAX_PIXELES', 25_000_000))        # 25 megapixeles (una foto de movil actual ronda 12-50)
MIN_LADO = 16
FORMATOS = {'JPEG', 'PNG'}
Image.MAX_IMAGE_PIXELS = MAX_PIXELES * 2     # Pillow avisa al superar este valor y falla al doble: nuestra comprobacion salta antes


def crear_app(carpeta_modelo):
    import mlflow.pyfunc
    modelo = mlflow.pyfunc.load_model(str(carpeta_modelo))
    lado = int(modelo.metadata.signature.inputs.inputs[0].shape[1])        # la firma es el contrato
    app = FastAPI(title='Perro o gato (pico)')

    @app.get('/salud')
    def salud():
        return {'estado': 'ok', 'lado_entrada': lado, 'clases': CLASES}

    @app.post('/predecir')
    def predecir(archivo: UploadFile = File(...)):
        t0 = time.perf_counter()
        datos = archivo.file.read(MAX_BYTES + 1)          # nunca se lee mas de MAX_BYTES + 1
        if not datos:
            raise HTTPException(400, 'Archivo vacio.')
        if len(datos) > MAX_BYTES:
            raise HTTPException(413, f'Archivo demasiado grande (maximo {MAX_BYTES // 1024} KB).')
        try:
            img = Image.open(io.BytesIO(datos))
            formato, (w, h) = img.format, img.size         # solo lee la cabecera
        except UnidentifiedImageError:
            raise HTTPException(415, 'El archivo no es una imagen reconocible.')
        except Image.DecompressionBombError:
            raise HTTPException(413, 'Imagen con demasiados pixeles.')
        if formato not in FORMATOS:
            raise HTTPException(415, f'Formato {formato} no admitido; use {sorted(FORMATOS)}.')
        if w * h > MAX_PIXELES:
            raise HTTPException(413, f'Imagen con demasiados pixeles ({w}x{h}).')
        if min(w, h) < MIN_LADO:
            raise HTTPException(422, f'Imagen demasiado pequena (minimo {MIN_LADO} px por lado).')
        try:
            x = preparar_imagen(img, lado)                 # decodifica de verdad: aqui salta una imagen truncada
        except (OSError, SyntaxError, ValueError):
            raise HTTPException(422, 'Imagen corrupta o incompleta.')
        salida = modelo.predict(x[None])                   # el sabor onnx de pyfunc devuelve un diccionario {nombre_de_salida: arreglo}
        p = np.asarray(next(iter(salida.values())) if isinstance(salida, dict) else salida)[0]
        return {'etiqueta': CLASES[int(p.argmax())], 'probabilidades': {c: round(float(v), 4) for c, v in zip(CLASES, p)},
                'entrada_original': {'formato': formato, 'ancho': w, 'alto': h}, 'ms': round((time.perf_counter() - t0) * 1000, 1)}

    return app


app = crear_app(os.environ['MODELO']) if 'MODELO' in os.environ else None     # uvicorn api_demo:app con MODELO=<carpeta>
