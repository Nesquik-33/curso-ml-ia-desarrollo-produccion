"""Etapa vivo: (a) curva de aprendizaje de la transferencia (cuantas fotos hacen falta), (b) cuanto pesaria el subconjunto repartible
(JPEG 128x128 calidad 90) y (c) ensayo de punta a punta de lo que se haria EN VIVO (con 2 nucleos): leer JPEG -> rasgos -> cabeza ->
ONNX -> registro MLflow con firma -> carga pyfunc -> prediccion, con el tiempo de cada fase."""
import io
import shutil
import time
from pathlib import Path

import numpy as np

import comun
from comun import TRABAJO, bootstrap_exactitud, guardar_json


def ejecutar(log):
    import torch
    torch.set_num_threads(2)
    import datos, redes
    from PIL import Image
    p, _ = datos.pets()
    ytr, yte = p['y_train'], p['y_test']
    xtr, xte = p['x_train_128'], p['x_test_128']
    rr = redes.mobilenet_rasgos()
    from sklearn.linear_model import LogisticRegression
    f_te = redes.rasgos_de(rr, 128, xte)
    rng = np.random.default_rng(comun.SEMILLA)
    out = {'curva_aprendizaje_mnet128_C0.1': []}
    for n in (10, 25, 50, 100, 300, 600, 1680):
        idx = np.concatenate([rng.permutation(np.flatnonzero(ytr == c))[:n] for c in (0, 1)])
        t = time.perf_counter()
        f = redes.rasgos_de(rr, 128, xtr[idx])
        m = LogisticRegression(C=0.1, max_iter=3000).fit(f, ytr[idx])
        seg = time.perf_counter() - t
        r = bootstrap_exactitud(yte, m.predict(f_te))
        r.update(por_clase=n, n_train=int(len(idx)), segundos_rasgos_y_cabeza=round(seg, 1))
        out['curva_aprendizaje_mnet128_C0.1'].append(r)
        log(f'  {n:>5} fotos por clase: test {r["exactitud"]:.4f} IC95 {r["ic95"]}  ({seg:.1f} s)')

    # (b) peso del subconjunto repartible: 600/clase train + 120/clase val (opcional) + 360/clase test, JPEG q90 128x128
    def jpeg(a, q=90):
        b = io.BytesIO(); Image.fromarray(a).save(b, format='JPEG', quality=q); return b.getvalue()
    sub = {}
    for q in (90, 80):
        total = 0
        n_img = 0
        for c in (0, 1):
            for x, y, n in ((xtr, ytr, 600), (xte, yte, 360)):
                for a in x[np.flatnonzero(y == c)[:n]]:
                    total += len(jpeg(a, q)); n_img += 1
        sub[f'jpeg_q{q}'] = {'imagenes': n_img, 'MB_total': round(total / 1e6, 2), 'KB_por_imagen': round(total / n_img / 1e3, 1)}
    out['subconjunto_repartible_600_por_clase_train_+_360_test'] = sub
    log(f'  subconjunto repartible: {sub}')

    # (c) ensayo en vivo con 600 por clase
    carpeta = TRABAJO / 'vivo'
    if carpeta.exists():
        shutil.rmtree(carpeta)
    (carpeta / 'img').mkdir(parents=True)
    idx = np.concatenate([np.flatnonzero(ytr == c)[:600] for c in (0, 1)])
    rutas, etq = [], ytr[idx]
    for k, i in enumerate(idx):
        r_ = carpeta / 'img' / f'{k:05d}.jpg'
        r_.write_bytes(jpeg(xtr[i], 90)); rutas.append(r_)
    fases = {}
    t = time.perf_counter()
    x = np.stack([np.asarray(Image.open(r_).convert('RGB')) for r_ in rutas])
    fases['1_leer_1200_jpeg_128px'] = time.perf_counter() - t
    t = time.perf_counter()
    f = redes.rasgos_de(rr, 128, x)
    fases['2_rasgos_mobilenet_1200_fotos'] = time.perf_counter() - t
    t = time.perf_counter()
    m = LogisticRegression(C=0.1, max_iter=3000).fit(f, etq)
    fases['3_ajustar_cabeza_logistica'] = time.perf_counter() - t
    cab = torch.nn.Linear(576, 2)
    w, b = m.coef_[0], m.intercept_[0]
    with torch.no_grad():
        cab.weight.copy_(torch.tensor(np.stack([-w / 2, w / 2]), dtype=torch.float32)); cab.bias.copy_(torch.tensor([-b / 2, b / 2], dtype=torch.float32))
    red = redes.Transferencia(128, rr, cab).eval()
    import onnx, mlflow, mlflow.onnx, mlflow.pyfunc
    from mlflow.models import ModelSignature
    from mlflow.types import Schema, TensorSpec
    from etapa_mlflow import exportar_onnx
    t = time.perf_counter()
    ruta_onnx = carpeta / 'modelo.onnx'
    exportar_onnx(red, x, ruta_onnx, log)
    fases['4_exportar_onnx'] = time.perf_counter() - t
    t = time.perf_counter()
    mlflow.set_tracking_uri(f'sqlite:///{(carpeta / "mlflow.db").as_posix()}')
    mlflow.set_experiment('vivo')
    firma = ModelSignature(inputs=Schema([TensorSpec(np.dtype('uint8'), (-1, 128, 128, 3), 'imagen')]),
                           outputs=Schema([TensorSpec(np.dtype('float32'), (-1, 2), 'probabilidades')]))
    with mlflow.start_run():
        acc = float((m.predict(redes.rasgos_de(rr, 128, xte)) == yte).mean())
        mlflow.log_metric('exactitud_test', acc)
        info = mlflow.onnx.log_model(onnx.load(str(ruta_onnx)), name='modelo', signature=firma, input_example=xte[:1],
                                     registered_model_name='perro-gato', onnx_execution_providers=['CPUExecutionProvider'],
                                     pip_requirements=['mlflow-skinny==3.18.0', 'onnxruntime', 'numpy'])
    fases['5_registrar_en_mlflow_con_firma'] = time.perf_counter() - t
    t = time.perf_counter()
    pf = mlflow.pyfunc.load_model('models:/perro-gato/1')
    pr = next(iter(pf.predict(xte[:5]).values()))
    fases['6_cargar_pyfunc_y_predecir_5'] = time.perf_counter() - t
    out['en_vivo_600_por_clase'] = {k: round(v, 1) for k, v in fases.items()}
    out['en_vivo_600_por_clase']['total_s'] = round(sum(fases.values()), 1)
    out['en_vivo_600_por_clase']['exactitud_test'] = bootstrap_exactitud(yte, m.predict(redes.rasgos_de(rr, 128, xte)))
    log(f'  en vivo: {out["en_vivo_600_por_clase"]}')
    shutil.rmtree(carpeta, ignore_errors=True)
    guardar_json('resultados_vivo.json', out)
