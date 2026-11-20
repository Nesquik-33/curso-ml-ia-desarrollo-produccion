"""Etapa paquetes: tamano REAL de las ruedas Linux x86_64 / Python 3.11 (las que instalaria la imagen python:3.11-slim) para tres opciones de servicio.
No instala nada: `pip download --platform ... --only-binary=:all:` en una carpeta temporal que se borra al final."""
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import comun
from comun import guardar_json

BASE = ['mlflow-skinny==3.18.0', 'numpy==2.4.6', 'pandas==2.3.3',  # pandas: mlflow.pyfunc lo importa y mlflow-skinny NO lo declara
         'pillow', 'fastapi==0.162.2', 'uvicorn==0.54.0', 'pydantic==2.14.3', 'python-multipart==0.0.33']
CONJUNTOS = {
    'A_onnxruntime': (BASE + ['onnxruntime'], []),
    'B_pytorch_cpu': (BASE + ['torch'], ['--extra-index-url', 'https://download.pytorch.org/whl/cpu']),
    'C_scikit_learn_(MLP)': (BASE + ['scikit-learn==1.9.1', 'scipy==1.17.1', 'joblib==1.6.0'], []),
}
PLAT = ['--platform', 'manylinux_2_28_x86_64', '--platform', 'manylinux_2_17_x86_64', '--platform', 'manylinux2014_x86_64', '--platform', 'manylinux_2_27_x86_64',
        '--platform', 'manylinux_2_34_x86_64', '--platform', 'manylinux_2_35_x86_64', '--platform', 'manylinux_2_39_x86_64', '--platform', 'any',
        '--python-version', '3.11', '--implementation', 'cp', '--abi', 'cp311', '--abi', 'abi3', '--abi', 'none', '--only-binary=:all:']


def ejecutar(log):
    out = {'plataforma_objetivo': 'Linux x86_64, CPython 3.11 (python:3.11-slim)', 'conjuntos': {}}
    tmp = Path(tempfile.mkdtemp(prefix='pico_ruedas_'))
    try:
        for nombre, (reqs, extra) in CONJUNTOS.items():
            d = tmp / nombre
            d.mkdir()
            cmd = [sys.executable, '-m', 'pip', 'download', '-q', '-d', str(d), *PLAT, *extra, *reqs]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=1500)
            if r.returncode != 0:
                out['conjuntos'][nombre] = {'error': r.stderr[-1000:]}
                log(f'{nombre}: FALLO {r.stderr[-300:]}')
                continue
            filas = []
            for w in sorted(d.iterdir()):
                comp = w.stat().st_size
                if w.suffix == '.whl':
                    with zipfile.ZipFile(w) as z:
                        desc = sum(i.file_size for i in z.infolist())
                else:
                    desc = comp
                filas.append((w.name.split('-')[0], w.name, comp, desc))
            filas.sort(key=lambda f: -f[3])
            out['conjuntos'][nombre] = {
                'peticiones': reqs, 'n_paquetes': len(filas),
                'ruedas_comprimidas_MB': round(sum(f[2] for f in filas) / 1e6, 1),
                'instalado_descomprimido_MB_(suma de ficheros de las ruedas)': round(sum(f[3] for f in filas) / 1e6, 1),
                'mayores': [{'paquete': f[1], 'comprimida_MB': round(f[2] / 1e6, 1), 'descomprimida_MB': round(f[3] / 1e6, 1)} for f in filas[:6]],
                'todos': sorted(f[1] for f in filas)}
            o = out['conjuntos'][nombre]
            log(f'{nombre}: {o["n_paquetes"]} paquetes, ruedas {o["ruedas_comprimidas_MB"]} MB, descomprimido {o["instalado_descomprimido_MB_(suma de ficheros de las ruedas)"]} MB; mayores: '
                f'{[(m["paquete"], m["descomprimida_MB"]) for m in o["mayores"][:3]]}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # imagen base: tamano comprimido del tag oficial (Docker Hub); solo para estimar
    try:
        t = json.loads(urllib.request.urlopen('https://hub.docker.com/v2/repositories/library/python/tags/3.11-slim', timeout=30).read())
        amd = [i for i in t.get('images', []) if i.get('architecture') == 'amd64' and i.get('os') == 'linux']
        out['python_3.11-slim_amd64_comprimida_MB'] = round(amd[0]['size'] / 1e6, 1) if amd else None
        out['python_3.11-slim_actualizada'] = t.get('last_updated')
    except Exception as e:
        out['python_3.11-slim_amd64_comprimida_MB'] = f'no disponible: {e}'
    log(f'imagen base: {out["python_3.11-slim_amd64_comprimida_MB"]} MB comprimida')
    guardar_json('resultados_paquetes.json', out)

