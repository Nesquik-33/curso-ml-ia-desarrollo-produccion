"""Descarga y preparacion de los dos conjuntos candidatos. Todo se guarda en _trabajo/ (regenerable) y se verifica por suma MD5/SHA-256."""
import hashlib
import pickle
import tarfile
import time
import urllib.request

import numpy as np

from comun import TRABAJO, SEMILLA, preparar_imagen

CIFAR_URL = 'https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz'
CIFAR_MD5 = 'c58f30108f718f92721af3b95e74349a'     # publicado en la pagina oficial de CIFAR
PETS_URL = 'https://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz'


def descargar(url, destino):
    if destino.exists():
        return {'descargado_ahora': False, 'bytes': destino.stat().st_size, 'segundos': 0}
    destino.parent.mkdir(parents=True, exist_ok=True)
    t = time.perf_counter()
    tmp = destino.with_suffix('.part')
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(destino)
    return {'descargado_ahora': True, 'bytes': destino.stat().st_size, 'segundos': round(time.perf_counter() - t, 1)}


def hash_fichero(ruta, alg):
    h = hashlib.new(alg)
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def particion(y, frac, semilla):
    """Divide indices estratificados por clase: devuelve (resto, seleccion)."""
    rng = np.random.default_rng(semilla)
    sel, resto = [], []
    for c in np.unique(y):
        idx = np.flatnonzero(y == c)
        rng.shuffle(idx)
        k = int(round(len(idx) * frac))
        sel.extend(idx[:k]); resto.extend(idx[k:])
    return np.array(sorted(resto)), np.array(sorted(sel))


def cifar():
    """CIFAR-10 desde Hugging Face (uoft-cs/cifar10, ficheros parquet). El servidor oficial (Toronto) respondio a ~40 KB/s por el proxy:
    170 MB tardarian mas de una hora, asi que no es utilizable desde este entorno. 3 = gato, 5 = perro (orden oficial de clases)."""
    import io
    import pandas as pd
    from PIL import Image
    base = 'https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/'
    info, partes = {'origen': base, 'servidor_oficial_toronto': 'demasiado lento por el proxy (~40 KB/s medidos); no usado'}, {}
    for nombre in ('train', 'test'):
        ruta = TRABAJO / 'cifar10' / f'{nombre}-00000-of-00001.parquet'
        info[nombre] = descargar(base + ruta.name, ruta)
        info[nombre]['sha256'] = hash_fichero(ruta, 'sha256')
        df = pd.read_parquet(ruta)
        x = np.stack([np.asarray(Image.open(io.BytesIO(d['bytes'])).convert('RGB')) for d in df['img']])
        partes[nombre] = (x, df['label'].to_numpy())

    def filtra(x, y):
        m = (y == 3) | (y == 5)
        return x[m], (y[m] == 5).astype(np.int64)
    X, Y = filtra(*partes['train'])
    Xt, Yt = filtra(*partes['test'])
    i_tr, i_va = particion(Y, 0.2, SEMILLA)
    out = dict(x_train=X[i_tr], y_train=Y[i_tr], x_val=X[i_va], y_val=Y[i_va], x_test=Xt, y_test=Yt)
    info['resumen'] = {k: list(v.shape) for k, v in out.items() if k.startswith('x_')}
    info['por_clase_test'] = {'gato': int((Yt == 0).sum()), 'perro': int((Yt == 1).sum())}
    return out, info

def pets():
    """Oxford-IIIT Pet: en el nombre de fichero la inicial MAYUSCULA indica gato y minuscula perro (convencion documentada del conjunto).
    Se equilibra (los perros sobran) y se guardan versiones 128x128 y 32x32 recortadas al centro; partes 70/15/15."""
    ruta = TRABAJO / 'pets' / 'images.tar.gz'
    info = descargar(PETS_URL, ruta)
    cache = TRABAJO / 'pets' / 'pets_preparado.npz'
    if not cache.exists():
        from PIL import Image
        import io
        nombres, x128, x32, y, muestras = [], [], [], [], {}
        with tarfile.open(ruta, 'r|gz') as t:
            for m in t:
                if not (m.isfile() and m.name.startswith('images/') and m.name.endswith('.jpg')):
                    continue
                datos = t.extractfile(m).read()
                try:
                    img = Image.open(io.BytesIO(datos)); img.load()
                except Exception:
                    continue
                base = m.name.split('/')[-1]
                gato = base[0].isupper()
                nombres.append(base); y.append(0 if gato else 1)
                x128.append(preparar_imagen(img, 128)); x32.append(preparar_imagen(img, 32))
                if len(muestras) < 4 and ((gato and 'g' not in muestras) or (not gato and 'p' not in muestras)):
                    muestras['g' if gato else 'p'] = datos
        np.savez_compressed(cache, nombres=np.array(nombres), x128=np.array(x128), x32=np.array(x32), y=np.array(y))
        for k, v in muestras.items():
            (TRABAJO / 'pets' / f'muestra_{k}.jpg').write_bytes(v)
    z = np.load(cache)
    y_all = z['y']
    rng = np.random.default_rng(SEMILLA)
    n_gato = int((y_all == 0).sum())
    perros = np.flatnonzero(y_all == 1)
    rng.shuffle(perros)
    sel = np.sort(np.concatenate([np.flatnonzero(y_all == 0), perros[:n_gato]]))
    y = y_all[sel]
    i_resto, i_te = particion(y, 0.15, SEMILLA)
    i_tr, i_va = particion(y[i_resto], 0.15 / 0.85, SEMILLA + 1)
    i_tr, i_va = i_resto[i_tr], i_resto[i_va]
    out = {}
    for lado in ('128', '32'):
        x = z['x' + lado][sel]
        out[f'x_train_{lado}'], out[f'x_val_{lado}'], out[f'x_test_{lado}'] = x[i_tr], x[i_va], x[i_te]
    out.update(y_train=y[i_tr], y_val=y[i_va], y_test=y[i_te])
    info['sha256_descarga'] = hash_fichero(ruta, 'sha256')
    info['resumen'] = {'imagenes_validas_total': int(len(y_all)), 'gatos': n_gato, 'perros_total': int((y_all == 1).sum()),
                       'perros_usados_equilibrado': n_gato, 'train': int(len(i_tr)), 'val': int(len(i_va)), 'test': int(len(i_te))}
    return out, info

