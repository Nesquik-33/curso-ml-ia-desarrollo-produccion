"""Se ejecuta con el Python de un venv LIMPIO (solo lo que instala una imagen de servicio: mlflow-skinny, onnxruntime, numpy, pillow...).
Carga el modelo con mlflow.pyfunc, predice y guarda las probabilidades. Informa de que NO hay torch ni scikit-learn cargados.
Uso: python verificar_limpio.py <carpeta_modelo_mlflow> <entrada.npy (uint8 NHWC) o carpeta con .png> <salida.npy> [bytes]"""
import io
import json
import sys
import time

t0 = time.perf_counter()
import mlflow
import mlflow.pyfunc
import numpy as np

t_import = time.perf_counter() - t0
carpeta, entrada, salida = sys.argv[1:4]
modo_bytes = len(sys.argv) > 4 and sys.argv[4] == 'bytes'
t1 = time.perf_counter()
modelo = mlflow.pyfunc.load_model(carpeta)
t_carga = time.perf_counter() - t1
x = np.load(entrada, allow_pickle=True)
if modo_bytes:
    import pandas as pd
    entrada_modelo = pd.DataFrame({'imagen': list(x)})
else:
    entrada_modelo = x
t2 = time.perf_counter()
p = modelo.predict(entrada_modelo)
t_pred = time.perf_counter() - t2
if isinstance(p, dict):
    p = next(iter(p.values()))
p = np.asarray(p.to_numpy() if hasattr(p, 'to_numpy') else p)
if p.dtype == object:
    p = np.stack([np.asarray(v) for v in p.ravel()])
np.save(salida, p.astype(np.float32).reshape(len(x), -1))
print(json.dumps({'mlflow': mlflow.__version__, 'python': sys.version.split()[0],
                  'torch_cargado': 'torch' in sys.modules, 'sklearn_cargado': 'sklearn' in sys.modules,
                  'pandas_cargado': 'pandas' in sys.modules,
                  'segundos_import_mlflow': round(t_import, 2), 'segundos_carga_modelo': round(t_carga, 2),
                  'segundos_prediccion_lote': round(t_pred, 3), 'n': int(len(x))}))

