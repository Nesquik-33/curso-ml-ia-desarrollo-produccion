"""Pico tecnico: extra de red neuronal (S3). Etapas (cada una guarda su salida en salidas/):
  datos     descarga CIFAR-10 y Oxford-IIIT Pet, comprueba sumas y reparto
  modelos   entrena y mide (2 nucleos): baselines sklearn, CNN propia, MobileNetV3-small con cabeza; bootstrap sobre el test
  mlflow    exporta a ONNX, registra con firma en MLflow, compara predicciones por todos los caminos, entorno limpio, tiempos
  api       pruebas de la API de subida de imagen (FastAPI TestClient)
  vivo      curva de aprendizaje, peso del subconjunto repartible y ensayo de punta a punta con tiempos por fase
  paquetes  tamanos de ruedas Linux (pip download) para PyTorch frente a ONNX Runtime frente a scikit-learn
Uso:  python pico.py <etapa> [--limpio <python de un venv limpio>]
Ejecutar con un venv TEMPORAL (torch CPU, torchvision, onnx, onnxruntime, mlflow, fastapi, httpx); no se instala nada en entornos compartidos."""
import argparse
import json
import platform
import sys
import time

import numpy as np

import comun
from comun import bootstrap_exactitud, guardar_json


def log(s=''):
    print(s, flush=True)


def etapa_datos():
    import datos
    res = {}
    for nombre, f in (('cifar10_gato_perro', datos.cifar), ('oxford_iiit_pet_gato_perro', datos.pets)):
        log(f'--- {nombre}')
        try:
            _, info = f()
            res[nombre] = info
            log(json.dumps(info, indent=2, ensure_ascii=False))
        except Exception as e:
            res[nombre] = {'error': f'{type(e).__name__}: {e}'}
            log(f'  FALLO: {e}')
    res['red'] = comprobar_red()
    guardar_json('resultados_datos.json', res)


def comprobar_red():
    import urllib.request
    urls = {
        'pypi': 'https://pypi.org/simple/pip/',
        'indice_pytorch_cpu': 'https://download.pytorch.org/whl/cpu/torch/',
        'pesos_torchvision': 'https://download.pytorch.org/models/mobilenet_v3_small-047dcff4.pth',
        'cifar_toronto': 'https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz',
        'cifar_huggingface': 'https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/train-00000-of-00001.parquet',
        'oxford_pets': 'https://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz',
        'tensorflow_cats_and_dogs_filtered': 'https://storage.googleapis.com/download.tensorflow.org/data/cats_and_dogs_filtered.zip',
        'huggingface_cats_vs_dogs_readme': 'https://huggingface.co/datasets/microsoft/cats_vs_dogs/raw/main/README.md',
    }
    out = {}
    for k, u in urls.items():
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, method='HEAD'), timeout=20)
            out[k] = {'estado': r.status, 'bytes': r.headers.get('Content-Length')}
        except Exception as e:
            out[k] = {'error': str(e)}
        log(f'  red {k}: {out[k]}')
    return out


def evalua(nombre, y, p):
    r = bootstrap_exactitud(y, p.argmax(1) if p.ndim > 1 else p)
    log(f'  {nombre}: exactitud={r["exactitud"]:.4f}  IC95={r["ic95"]}  n={r["n_test"]}')
    return r


def etapa_modelos():
    import torch
    torch.set_num_threads(2)
    import datos, redes
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    log(f'torch {torch.__version__}, hilos={torch.get_num_threads()}, {json.dumps(comun.cpu_info())}')
    out = {'equipo': comun.cpu_info(), 'torch': torch.__version__, 'hilos': 2, 'modelos': {}}
    (comun.TRABAJO / 'modelos').mkdir(exist_ok=True)

    def guardar(clave, red=None, extra=None):
        if red is not None:
            ruta = comun.TRABAJO / 'modelos' / f'{clave}.pt'
            torch.save(red, ruta)
            extra['tamano_pt_MB'] = round(ruta.stat().st_size / 1e6, 2)
        out['modelos'][clave] = extra
        guardar_json('resultados_modelos.json', out)

    # ---------------- CIFAR-10 gato/perro
    d, _ = datos.cifar()
    xtr, ytr, xva, yva, xte, yte = d['x_train'], d['y_train'], d['x_val'], d['y_val'], d['x_test'], d['y_test']
    log(f'\n=== CIFAR-10 gato/perro: train={len(ytr)} val={len(yva)} test={len(yte)}')
    flat = lambda x: x.reshape(len(x), -1).astype(np.float32) / 255
    t = time.perf_counter()
    lr = LogisticRegression(max_iter=300).fit(flat(xtr), ytr)
    seg = time.perf_counter() - t
    guardar('cifar_lr_pixeles', None, {'segundos_entrenamiento': round(seg, 1), 'val': round(float((lr.predict(flat(xva)) == yva).mean()), 4),
                                       'test': evalua('cifar LR sobre pixeles', yte, lr.predict(flat(xte)))})
    t = time.perf_counter()
    mlp = MLPClassifier((256,), max_iter=40, random_state=comun.SEMILLA).fit(flat(xtr), ytr)
    seg = time.perf_counter() - t
    guardar('cifar_mlp_pixeles', None, {'segundos_entrenamiento': round(seg, 1), 'val': round(float((mlp.predict(flat(xva)) == yva).mean()), 4),
                                        'parametros': int(sum(c.size for c in mlp.coefs_) + sum(c.size for c in mlp.intercepts_)),
                                        'test': evalua('cifar MLP sklearn (256) sobre pixeles', yte, mlp.predict(flat(xte)))})
    log('  CNN propia (32x32), 20 epocas')
    red, inf = redes.entrenar_cnn(32, xtr, ytr, xva, yva, 20, log)
    inf['test'] = evalua('cifar CNN propia', yte, redes.proba(red, xte))
    inf['inferencia_1_imagen_torch'] = redes.tiempo_inferencia_torch(red, xte)
    guardar('cifar_cnn', red, inf)
    for lado in (64, 96, 128):
        log(f'  MobileNetV3-small congelada, entrada reescalada a {lado}')
        red, inf = redes.entrenar_transferencia(lado, xtr, ytr, xva, yva, log)
        inf['test'] = evalua(f'cifar mobilenet@{lado}', yte, redes.proba(red, xte))
        inf['inferencia_1_imagen_torch'] = redes.tiempo_inferencia_torch(red, xte)
        guardar(f'cifar_mnet_{lado}', red, inf)

    # ---------------- Oxford-IIIT Pet gato/perro (fotos reales)
    p, _ = datos.pets()
    ytr, yva, yte = p['y_train'], p['y_val'], p['y_test']
    log(f'\n=== Oxford-IIIT Pet gato/perro equilibrado: train={len(ytr)} val={len(yva)} test={len(yte)}')
    log('  CNN propia (64x64 desde 128), 20 epocas')
    red, inf = redes.entrenar_cnn(64, p['x_train_128'], ytr, p['x_val_128'], yva, 20, log)
    inf['test'] = evalua('pets CNN propia 64', yte, redes.proba(red, p['x_test_128']))
    inf['inferencia_1_imagen_torch'] = redes.tiempo_inferencia_torch(red, p['x_test_128'])
    guardar('pets_cnn', red, inf)
    for lado in (96, 128):
        log(f'  MobileNetV3-small congelada, entrada {lado}')
        red, inf = redes.entrenar_transferencia(lado, p['x_train_128'], ytr, p['x_val_128'], yva, log)
        inf['test'] = evalua(f'pets mobilenet@{lado}', yte, redes.proba(red, p['x_test_128']))
        inf['inferencia_1_imagen_torch'] = redes.tiempo_inferencia_torch(red, p['x_test_128'])
        guardar(f'pets_mnet_{lado}', red, inf)

    # ---------------- desplazamiento de dominio: modelos CIFAR frente a FOTOS reales reducidas a 32x32 (test de pets)
    log('\n=== Modelos entrenados con CIFAR frente a fotos reales (pets test) reducidas a 32x32')
    desp = {}
    for clave in ('cifar_cnn', 'cifar_mnet_64', 'cifar_mnet_96', 'cifar_mnet_128'):
        red = torch.load(comun.TRABAJO / 'modelos' / f'{clave}.pt', weights_only=False)
        desp[clave] = evalua(clave + ' sobre fotos pets@32', yte, redes.proba(red, p['x_test_32']))
    out['desplazamiento_cifar_a_fotos_32'] = desp
    guardar_json('resultados_modelos.json', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('etapa', choices=['datos', 'modelos', 'mlflow', 'api', 'paquetes', 'vivo'])
    ap.add_argument('--limpio', help='python de un venv limpio (solo serving) para la etapa mlflow')
    a = ap.parse_args()
    comun.limitar_a_dos_nucleos()
    comun.iniciar_salida(a.etapa)
    log(f'python {platform.python_version()}  {time.strftime("%Y-%m-%d %H:%M:%S")}')
    if a.etapa == 'datos':
        etapa_datos()
    elif a.etapa == 'modelos':
        etapa_modelos()
    elif a.etapa == 'mlflow':
        import etapa_mlflow
        etapa_mlflow.ejecutar(a.limpio, log)
    elif a.etapa == 'api':
        import pruebas_api
        pruebas_api.ejecutar(log)
    elif a.etapa == 'vivo':
        import etapa_vivo
        etapa_vivo.ejecutar(log)
    elif a.etapa == 'paquetes':
        import etapa_paquetes
        etapa_paquetes.ejecutar(log)


if __name__ == '__main__':
    main()

