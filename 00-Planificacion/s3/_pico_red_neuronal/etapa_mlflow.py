"""Etapa mlflow: ONNX + registro con firma + todos los caminos de prediccion + entorno limpio + tiempos. Sobre los finalistas."""
import io
import json
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

import comun
from comun import TRABAJO, bootstrap_exactitud, guardar_json, cargar_json, png_bytes


def tam_carpeta(p):
    return sum(f.stat().st_size for f in Path(p).rglob('*') if f.is_file())


def exportar_onnx(red, ejemplo, ruta, log):
    import torch
    from redes import ConSoftmax
    m = ConSoftmax(red).eval()
    x = torch.from_numpy(ejemplo[:1])
    try:
        torch.onnx.export(m, (x,), str(ruta), input_names=['imagen'], output_names=['probabilidades'],
                          dynamic_axes={'imagen': {0: 'lote'}, 'probabilidades': {0: 'lote'}}, opset_version=17, dynamo=False)
        return 'exportador clasico (dynamo=False), opset 17'
    except Exception as e:
        log(f'    exportador clasico fallo ({type(e).__name__}: {str(e)[:150]}); pruebo dynamo')
        torch.onnx.export(m, (x,), str(ruta), input_names=['imagen'], output_names=['probabilidades'],
                          dynamic_shapes={'x': {0: torch.export.Dim('lote')}}, opset_version=18, dynamo=True)
        return 'exportador dynamo, opset 18'


def lanzar_limpio(py, carpeta, entrada, salida, modo=''):
    cmd = [py, str(comun.AQUI / 'verificar_limpio.py'), str(carpeta), str(entrada), str(salida)] + ([modo] if modo else [])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        return {'error': r.stderr[-800:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def a_array(p):
    if isinstance(p, dict):
        p = next(iter(p.values()))
    return np.asarray(p.to_numpy() if hasattr(p, 'to_numpy') else p, dtype=np.float32)


def tiempo_ms(f, n=200, calentar=20):
    for _ in range(calentar):
        f()
    t = []
    for _ in range(n):
        a = time.perf_counter(); f(); t.append((time.perf_counter() - a) * 1000)
    return {'mediana_ms': round(float(np.median(t)), 2), 'p95_ms': round(float(np.percentile(t, 95)), 2)}


def elegir(res, prefijo):
    c = {k: v for k, v in res['modelos'].items() if k.startswith(prefijo)}
    return max(c, key=lambda k: c[k]['mejor_val'] if 'mejor_val' in c[k] else -1)


def ejecutar(limpio, log):
    import mlflow, mlflow.onnx, mlflow.pyfunc, onnx, onnxruntime as ort, torch
    from mlflow.models import ModelSignature, infer_signature
    from mlflow.types import Schema, TensorSpec, ColSpec
    import datos
    torch.set_num_threads(2)
    res = cargar_json('resultados_modelos.json')
    cif, _ = datos.cifar()
    pet, _ = datos.pets()
    finalistas = {
        'cifar_cnn': (cif['x_test'], cif['y_test']),
        elegir(res, 'cifar_mnet'): (cif['x_test'], cif['y_test']),
        elegir(res, 'pets_mnet'): (pet['x_test_128'], pet['y_test']),
    }
    log(f'finalistas: {list(finalistas)}   mlflow {mlflow.__version__}  onnxruntime {ort.__version__}  onnx {onnx.__version__}')
    base = TRABAJO / 'mlflow_pico'
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    mlflow.set_tracking_uri(f'sqlite:///{(base / "mlflow.db").as_posix()}')
    mlflow.set_experiment('pico-perro-gato')
    salida = {'versiones': {'mlflow': mlflow.__version__, 'onnxruntime': ort.__version__, 'onnx': onnx.__version__, 'torch': torch.__version__},
              'limpio': None, 'modelos': {}}
    pip_req = [f'mlflow-skinny=={mlflow.__version__}', f'onnxruntime=={ort.__version__}', f'numpy=={np.__version__}']

    for clave, (xte, yte) in finalistas.items():
        log(f'\n=== {clave}')
        r = {}
        red = torch.load(TRABAJO / 'modelos' / f'{clave}.pt', weights_only=False).eval()
        from redes import proba
        p_torch = proba(red, xte)
        r['exactitud_torch_test'] = bootstrap_exactitud(yte, p_torch.argmax(1))
        onnx_ruta = base / f'{clave}.onnx'
        r['exportador'] = exportar_onnx(red, xte, onnx_ruta, log)
        r['tamano_onnx_MB'] = round(onnx_ruta.stat().st_size / 1e6, 3)
        r['tamano_pt_MB'] = round((TRABAJO / 'modelos' / f'{clave}.pt').stat().st_size / 1e6, 3)
        onnx.checker.check_model(onnx.load(str(onnx_ruta)))
        so = ort.SessionOptions(); so.intra_op_num_threads = 2
        ses = ort.InferenceSession(str(onnx_ruta), so, providers=['CPUExecutionProvider'])
        p_ort = np.concatenate([ses.run(None, {'imagen': xte[i:i + 256]})[0] for i in range(0, len(xte), 256)])

        lado = xte.shape[1]
        firma = ModelSignature(inputs=Schema([TensorSpec(np.dtype('uint8'), (-1, lado, lado, 3), 'imagen')]),
                               outputs=Schema([TensorSpec(np.dtype('float32'), (-1, 2), 'probabilidades')]))
        with mlflow.start_run(run_name=clave) as run:
            mlflow.log_params({'modelo': clave, 'lado_entrada': lado, 'clases': 'gato,perro'})
            mlflow.log_metric('exactitud_test', r['exactitud_torch_test']['exactitud'])
            info = mlflow.onnx.log_model(onnx.load(str(onnx_ruta)), name='modelo', signature=firma, input_example=xte[:2],
                                         registered_model_name=f'pico-{clave}', pip_requirements=pip_req, onnx_execution_providers=['CPUExecutionProvider'])
        r['firma'] = {'entrada': str(firma.inputs), 'salida': str(firma.outputs)}
        r['uri_registro'] = info.model_uri
        carpeta = base / f'modelo_mlflow_{clave}'
        mlflow.onnx.save_model(onnx.load(str(onnx_ruta)), str(carpeta), signature=firma, input_example=xte[:2], pip_requirements=pip_req, onnx_execution_providers=['CPUExecutionProvider'])
        r['tamano_carpeta_mlflow_MB'] = round(tam_carpeta(carpeta) / 1e6, 3)
        r['ficheros_carpeta_mlflow'] = sorted(f.name for f in carpeta.iterdir())
        r['requirements_txt'] = (carpeta / 'requirements.txt').read_text().split()

        caminos = {'onnxruntime_directo': p_ort}
        pf = mlflow.pyfunc.load_model(str(carpeta))
        caminos['mlflow.pyfunc (carpeta, mlflow completo)'] = a_array(pf.predict(xte))
        caminos['mlflow.pyfunc (models:/ del registro)'] = a_array(mlflow.pyfunc.load_model(f'models:/pico-{clave}/1').predict(xte))
        np.save(base / 'entrada.npy', xte)
        if limpio:
            o = base / 'salida_limpio.npy'
            r['limpio_info'] = lanzar_limpio(limpio, carpeta, base / 'entrada.npy', o)
            if 'error' not in r['limpio_info']:
                caminos['mlflow.pyfunc (venv limpio con mlflow-skinny)'] = np.load(o)
        r['comparacion_con_torch'] = {k: {'max_dif_abs_prob': float(np.abs(v - p_torch).max()),
                                           'predicciones_distintas': int((v.argmax(1) != p_torch.argmax(1)).sum()), 'n': int(len(v))}
                                       for k, v in caminos.items()}
        for k, v in r['comparacion_con_torch'].items():
            log(f'  {k}: max|dif|={v["max_dif_abs_prob"]:.2e}  predicciones distintas={v["predicciones_distintas"]}/{v["n"]}')
        # tipos de entrada que acepta pyfunc con la firma tensor
        pruebas = {}
        for nombre, f in {'float32 en vez de uint8': lambda: xte[:2].astype(np.float32),
                          'forma equivocada (sin canal)': lambda: xte[:2, :, :, 0],
                          'lado distinto (+1 pixel)': lambda: np.pad(xte[:2], ((0, 0), (0, 1), (0, 1), (0, 0))),
                          'una sola imagen sin lote': lambda: xte[0]}.items():
            try:
                pf.predict(f()); pruebas[nombre] = 'acepta'
            except Exception as e:
                pruebas[nombre] = f'{type(e).__name__}: {str(e)[:160]}'
        r['entradas_invalidas_pyfunc'] = pruebas
        for k, v in pruebas.items():
            log(f'  entrada {k}: {v}')

        # tiempos con 2 hilos, lote de 1
        x1 = xte[:1]
        r['inferencia_1_imagen_ms'] = {'onnxruntime': tiempo_ms(lambda: ses.run(None, {'imagen': x1})),
                                       'mlflow.pyfunc': tiempo_ms(lambda: pf.predict(x1), n=100)}
        from redes import tiempo_inferencia_torch
        r['inferencia_1_imagen_ms']['torch_eager'] = tiempo_inferencia_torch(red, xte)
        log(f'  tiempos 1 imagen: {r["inferencia_1_imagen_ms"]}')

        # ---- modelo con BYTES de imagen (pyfunc propio): PNG sin perdida y JPEG con perdida
        fir_b = ModelSignature(inputs=Schema([ColSpec('binary', 'imagen')]), outputs=Schema([TensorSpec(np.dtype('float32'), (-1, 2), 'probabilidades')]))
        carpeta_b = base / f'modelo_bytes_{clave}'
        import pandas as pd
        n = min(len(xte), 600)
        from PIL import Image
        def jpeg(a, q):
            b = io.BytesIO(); Image.fromarray(a).save(b, format='JPEG', quality=q); return b.getvalue()
        ej = pd.DataFrame({'imagen': [png_bytes(xte[0])]})
        mlflow.pyfunc.save_model(str(carpeta_b), python_model=str(comun.AQUI / 'modelo_bytes.py'), artifacts={'onnx': str(onnx_ruta)},
                                 signature=fir_b, input_example=ej, pip_requirements=pip_req + ['pillow'], code_paths=[str(comun.AQUI / 'comun.py')])
        pb = mlflow.pyfunc.load_model(str(carpeta_b))
        png = [png_bytes(a) for a in xte[:n]]
        p_png = np.asarray(pb.predict(pd.DataFrame({'imagen': png})))
        rb = {'n': n, 'png_max_dif_abs_prob_vs_torch': float(np.abs(p_png - p_torch[:n]).max()),
              'png_predicciones_distintas': int((p_png.argmax(1) != p_torch[:n].argmax(1)).sum()),
              'tamano_carpeta_MB': round(tam_carpeta(carpeta_b) / 1e6, 3)}
        np.save(base / 'entrada_png.npy', np.array(png, dtype=object))
        if limpio:
            o = base / 'salida_limpio_bytes.npy'
            info_l = lanzar_limpio(limpio, carpeta_b, base / 'entrada_png.npy', o, 'bytes')
            rb['limpio_info'] = info_l
            if 'error' not in info_l:
                rb['limpio_png_max_dif_abs_prob_vs_torch'] = float(np.abs(np.load(o) - p_torch[:n]).max())
        for q in (95, 85, 70):
            pj = np.asarray(pb.predict(pd.DataFrame({'imagen': [jpeg(a, q) for a in xte[:n]]})))
            rb[f'jpeg_q{q}'] = {'predicciones_distintas_vs_png': int((pj.argmax(1) != p_png.argmax(1)).sum()),
                                'max_dif_abs_prob': round(float(np.abs(pj - p_png).max()), 4),
                                'exactitud': bootstrap_exactitud(yte[:n], pj.argmax(1))}
        rb['exactitud_png_mismas_filas'] = bootstrap_exactitud(yte[:n], p_png.argmax(1))
        # foto real grande (jpg original del conjunto Pet) de principio a fin
        foto = TRABAJO / 'pets' / 'muestra_g.jpg'
        if foto.exists():
            fb = foto.read_bytes()
            df1 = pd.DataFrame({'imagen': [fb]})
            rb['foto_real'] = {'bytes': len(fb), 'dimensiones': list(Image.open(io.BytesIO(fb)).size),
                               'probabilidades_[gato,perro]': [round(float(v), 4) for v in np.asarray(pb.predict(df1))[0]],
                               'etiqueta_real': 'gato (nombre de fichero)', 'tiempo_ms_pyfunc_bytes': tiempo_ms(lambda: pb.predict(df1), n=60, calentar=5)}
        r['modelo_bytes'] = rb
        log(f'  bytes: PNG max dif={rb["png_max_dif_abs_prob_vs_torch"]:.2e} distintas={rb["png_predicciones_distintas"]}/{n}; '
            f'JPEG q95/85/70 distintas vs PNG: {[rb[f"jpeg_q{q}"]["predicciones_distintas_vs_png"] for q in (95, 85, 70)]}')
        log(f'  foto real: {rb.get("foto_real")}')
        salida['modelos'][clave] = r
        guardar_json('resultados_mlflow.json', salida)

    if limpio:
        sp = Path(limpio).resolve().parent.parent / 'Lib' / 'site-packages'
        if not sp.exists():
            sp = Path(limpio).resolve().parent.parent / 'lib' / 'site-packages'
        tam = {d.name: tam_carpeta(d) for d in sp.iterdir() if d.is_dir() and not d.name.endswith('.dist-info')}
        salida['limpio'] = {'site_packages_total_MB': round(tam_carpeta(sp) / 1e6, 1),
                            'mayores_MB': {k: round(v / 1e6, 1) for k, v in sorted(tam.items(), key=lambda kv: -kv[1])[:10]}}
        log(f'\nvenv limpio: {salida["limpio"]}')
    guardar_json('resultados_mlflow.json', salida)

