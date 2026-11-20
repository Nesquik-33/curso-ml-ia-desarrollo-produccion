"""Pruebas de la API de subida de imagen con el TestClient de FastAPI sobre el modelo MLflow del mejor finalista de fotos (pets) y del de CIFAR."""
import io
import time
import warnings

import numpy as np
from PIL import Image

import comun
from comun import TRABAJO, guardar_json, png_bytes


def ejecutar(log):
    from fastapi.testclient import TestClient
    import mlflow.pyfunc
    import api_demo
    import datos
    from etapa_mlflow import elegir
    res = comun.cargar_json('resultados_modelos.json')
    out = {}
    cif, _ = datos.cifar()
    pet, _ = datos.pets()
    for etiqueta, clave, xte, yte in (('fotos', elegir(res, 'pets_mnet'), pet['x_test_128'], pet['y_test']),
                                      ('cifar', 'cifar_cnn', cif['x_test'], cif['y_test'])):
        log(f'\n=== API sobre {clave}')
        carpeta = TRABAJO / 'mlflow_pico' / f'modelo_mlflow_{clave}'
        app = api_demo.crear_app(carpeta)
        c = TestClient(app)
        directo = mlflow.pyfunc.load_model(str(carpeta))
        r = {'salud': c.get('/salud').json()}
        casos = {}

        def post(nombre, contenido, nombre_fichero='f.png', tipo='image/png'):
            a = time.perf_counter()
            resp = c.post('/predecir', files={'archivo': (nombre_fichero, contenido, tipo)})
            ms = round((time.perf_counter() - a) * 1000, 1)
            try:
                cuerpo = resp.json()
            except Exception:
                cuerpo = resp.text[:100]
            casos[nombre] = {'http': resp.status_code, 'ms': ms, 'cuerpo': cuerpo if resp.status_code != 200 else {k: cuerpo[k] for k in ('etiqueta', 'probabilidades')}}
            log(f'  {nombre:<44} -> {resp.status_code}  {casos[nombre]["cuerpo"] if resp.status_code != 200 else casos[nombre]["cuerpo"]["probabilidades"]}  ({ms} ms)')
            return resp

        def buf(img, fmt, **kw):
            b = io.BytesIO(); img.save(b, format=fmt, **kw); return b.getvalue()

        # 1) coincidencia con el camino directo (PNG sin perdida) en 50 imagenes
        difs = []
        for i in range(50):
            p = post(f'png_test_{i}', png_bytes(xte[i])) if i < 3 else c.post('/predecir', files={'archivo': ('f.png', png_bytes(xte[i]), 'image/png')})
            pd_ = next(iter(directo.predict(xte[i:i + 1]).values()))[0]
            difs.append(abs(p.json()['probabilidades']['gato'] - float(pd_[0])))
        r['max_dif_api_vs_directo_(50 imagenes, redondeo a 4 decimales)'] = float(max(difs))
        base = Image.fromarray(xte[0])
        # 2) variantes de formato/modo
        post('RGBA con transparencia', buf(base.convert('RGBA'), 'PNG'))
        post('gris (L)', buf(base.convert('L'), 'PNG'))
        post('paleta (P)', buf(base.convert('P'), 'PNG'))
        post('JPEG CMYK', buf(base.convert('CMYK'), 'JPEG'), 'f.jpg', 'image/jpeg')
        # EXIF: foto girada guardada con orientacion 6 frente a la misma ya girada
        g = Image.fromarray(xte[1]).convert('RGB')
        ex = Image.Exif(); ex[274] = 6
        con_exif = post('JPEG con EXIF orientacion=6', buf(g, 'JPEG', exif=ex.tobytes(), quality=95), 'f.jpg', 'image/jpeg')
        girada = post('JPEG ya girado, sin EXIF', buf(g.rotate(-90, expand=True), 'JPEG', quality=95), 'f.jpg', 'image/jpeg')
        r['exif_aplicado_(las_dos_probabilidades_deben_ser_casi_iguales)'] = [con_exif.json()['probabilidades'], girada.json()['probabilidades']]
        # 3) fotos reales grandes
        for k in ('g', 'p'):
            ruta = TRABAJO / 'pets' / f'muestra_{k}.jpg'
            if ruta.exists():
                b = ruta.read_bytes()
                post(f'foto real {"gato" if k == "g" else "perro"} ({len(b) // 1024} KB, {Image.open(io.BytesIO(b)).size})', b, 'f.jpg', 'image/jpeg')
        grande = Image.effect_mandelbrot((4000, 3000), (-2, -1.2, 1, 1.2), 30).convert('RGB')
        post('JPEG 4000x3000 (12 MP, sintetica)', buf(grande, 'JPEG', quality=60), 'f.jpg', 'image/jpeg')
        # 4) entradas hostiles o erroneas
        post('archivo de texto con nombre .jpg', b'esto no es una imagen', 'f.jpg', 'image/jpeg')
        post('vacio', b'')
        post('2,5 MB de ruido PNG (> 2 MB)', buf(Image.fromarray(np.random.default_rng(0).integers(0, 255, (1000, 1000, 3), dtype=np.uint8)), 'PNG'))
        jpg = buf(base.resize((300, 300)), 'JPEG', quality=95)
        post('JPEG truncado a la mitad', jpg[:len(jpg) // 2], 'f.jpg', 'image/jpeg')
        post('GIF (no admitido)', buf(base, 'GIF'), 'f.gif', 'image/gif')
        post('WEBP (no admitido)', buf(base, 'WEBP'), 'f.webp', 'image/webp')
        post('muy pequena (8x8)', buf(base.resize((8, 8)), 'PNG'))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            bomba = buf(Image.new('L', (12000, 12000)), 'PNG')
        post(f'bomba de descompresion PNG 12000x12000 ({len(bomba) // 1024} KB)', bomba)
        resp = c.post('/predecir', files={'otro': ('f.png', png_bytes(xte[0]), 'image/png')})
        casos['campo "archivo" ausente'] = {'http': resp.status_code}
        log(f'  campo archivo ausente -> {resp.status_code}')
        # 5) latencia de extremo a extremo (cliente de prueba, sin red real), mediana de 40 peticiones
        t = []
        pngp = png_bytes(xte[0])
        for _ in range(40):
            a = time.perf_counter(); c.post('/predecir', files={'archivo': ('f.png', pngp, 'image/png')}); t.append((time.perf_counter() - a) * 1000)
        r['latencia_peticion_imagen_ya_del_tamano_del_modelo_ms'] = {'mediana': round(float(np.median(t)), 1), 'p95': round(float(np.percentile(t, 95)), 1)}
        ruta = TRABAJO / 'pets' / 'muestra_g.jpg'
        if ruta.exists():
            b = ruta.read_bytes(); t = []
            for _ in range(40):
                a = time.perf_counter(); c.post('/predecir', files={'archivo': ('f.jpg', b, 'image/jpeg')}); t.append((time.perf_counter() - a) * 1000)
            r['latencia_foto_real_jpeg_ms'] = {'mediana': round(float(np.median(t)), 1), 'p95': round(float(np.percentile(t, 95)), 1), 'bytes': len(b)}
        r['casos'] = casos
        out[etiqueta] = r
    guardar_json('resultados_api.json', out)
