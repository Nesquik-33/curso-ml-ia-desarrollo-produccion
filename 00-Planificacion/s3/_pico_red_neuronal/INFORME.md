# Informe del pico: extra de red neuronal en S3 (perro o gato)

Fecha: 15/11/2026. Todo se reproduce con `pico.py` (etapas `datos`, `modelos`, `mlflow`, `api`, `vivo`, `paquetes`); las salidas de la última ejecución de cada etapa están en `salidas/` (`resultados_*.json` y `salida_*.txt`). Lo descargado y los modelos generados van a `_trabajo/` (regenerable, fuera de git).

## Veredicto: **Sí, con cambios**

El extra es viable y cabe en 30 minutos si se entrena **en vivo solo la cabeza de una red ligera preentrenada** (unos 8 s de cómputo), se registra en MLflow con firma y se sirve con **ONNX Runtime** (imagen de unos 264 MB de paquetes frente a unos 982 MB con PyTorch). Los cambios respecto a la idea inicial:

1. **No entrenar una CNN propia en directo**: en 2 hilos tarda 9,4 min (CIFAR) o 11,9 min (fotos). Solo vale como modelo ya entrenado.
2. **No usar CIFAR-10 de 32×32 como demo principal**: con una CNN propia da 86,4 % en su propio test y 79 % con fotos reales reducidas a 32×32 (ver riesgos). Mejor fotos reales de Oxford-IIIT Pet a 128×128 (93,1 %).
3. **Servir con ONNX Runtime, no con PyTorch**: la imagen no necesita `torch`. Hay que añadir `pandas` a los requisitos aunque `mlflow-skinny` no lo declare (`mlflow.pyfunc` lo importa).
4. La API de la imagen debe hacer el preprocesado (recorte, redimensionado, formato) y validar la subida; el modelo solo recibe píxeles `uint8`.

## Combinación recomendada

| Pieza | Elección |
|---|---|
| Datos | Oxford-IIIT Pet, gatos frente a perros, equilibrado (2 400 + 2 400). En el repo: subconjunto de **1 920 JPEG de 128×128 (8,7 MB con calidad 80; 12,4 MB con calidad 90)** y atribución CC BY-SA 4.0 |
| Red | MobileNetV3-small preentrenada (ImageNet) **congelada** + regresión logística sobre sus 576 rasgos (entrada 128×128) |
| Biblioteca de entrenamiento | PyTorch CPU + torchvision (solo en el Codespace de entrenamiento) |
| Biblioteca de servicio | ONNX Runtime + `mlflow-skinny` (modelo ONNX de 3,7 MB con softmax y preprocesado dentro) |
| Plan B si no hay tiempo | Modelo ya entrenado y registrado, cargado desde la carpeta MLflow (3,8–6,5 MB) |

## Resumen de cifras clave

| Dato | Valor |
|---|---|
| Exactitud en test, fotos Oxford-IIIT Pet (n = 720), MobileNetV3-small + cabeza a 128×128 | **93,1 %** (IC95 bootstrap 91,1–94,9) |
| Misma, CNN propia a 64×64 desde 128 | 88,8 % (86,4–91,1) |
| Exactitud en test CIFAR-10 gato/perro (n = 2 000), CNN propia 32×32 | 86,4 % (84,8–88,0) |
| Misma, MobileNetV3-small + cabeza (entrada ampliada a 128) | 83,6 % (82,0–85,2) |
| Tiempo de entrenar en vivo (1 200 fotos, 2 hilos): leer JPEG + rasgos + cabeza | 1,5 s (7,6 s con exportar y registrar en MLflow) |
| Tiempo de entrenar la CNN propia (20 épocas, 2 hilos) | 566 s (CIFAR) y 713 s (fotos) |
| Predicción por todos los caminos | misma etiqueta en 2 000 de 2 000 (CIFAR) y 720 de 720 (fotos); diferencia máxima de probabilidad ≤ 1,3e-5 |
| Inferencia de 1 imagen (ONNX Runtime, 2 hilos) | 0,6–0,9 ms; con `mlflow.pyfunc` 0,5–0,9 ms; con PyTorch en memoria 2–4,6 ms |
| Paquetes de la imagen, descomprimidos (Linux, Python 3.11) | ONNX Runtime **263,5 MB**; scikit-learn (imagen actual de la API) 336,6 MB; PyTorch CPU **981,5 MB** |

## 1. Datos

### 1.1 Red y descargas (probado desde este equipo, con el proxy corporativo)

| Origen | Resultado |
|---|---|
| PyPI y índice de ruedas CPU de PyTorch | funcionan (`pip` descargó e instaló sin tocar el proxy) |
| Pesos `mobilenet_v3_small` de torchvision (10,3 MB) | funciona |
| CIFAR-10 en Hugging Face (`uoft-cs/cifar10`, parquet: 119,7 + 23,9 MB) | funciona y es rápido (unos 8 MB/s) |
| CIFAR-10 en el servidor oficial de Toronto (170,5 MB) | responde a las peticiones de cabecera, pero la descarga fue de **unos 40 KB/s** (35 MB en varios minutos; medición aproximada, sin instrumentar): inutilizable. Se abortó y no se usó |
| Oxford-IIIT Pet (`images.tar.gz`, 791,9 MB) | funciona: 73,8 s |
| `cats_and_dogs_filtered.zip` de TensorFlow (Google Storage) | **403 Prohibido** |
| Hugging Face `microsoft/cats_vs_dogs` | solo se comprobó la ficha (accesible); no se descargó (necesitaría ~0,8 GB y su licencia figura como «unknown») |

Hugging Face y los datos de torchvision se descargan por HTTPS normal; no se comprobó el acceso desde un Codespace (no medido).

### 1.2 Conjuntos medidos

| | CIFAR-10 gato/perro | Oxford-IIIT Pet gato/perro |
|---|---|---|
| Imágenes | 12 000 (10 000 de train oficial, 2 000 de test oficial), 32×32 | 7 390 (2 400 gatos, 4 990 perros), tamaño variable |
| Uso | train 8 000, val 2 000, test oficial 2 000 (1 000 + 1 000) | equilibrado a 2 400 por clase; train 3 360, val 720, test 720; se guardan a 128×128 (recorte centrado) |
| Etiqueta | clases 3 y 5 del conjunto | inicial mayúscula en el nombre de fichero = gato; coherente con 2 400 gatos (12 razas × 200) y 4 990 perros |
| Descarga | 143,6 MB (parquet) | 791,9 MB (`sha256` en `salidas/resultados_datos.json`) |
| Licencia | **no declarada**: la ficha de Hugging Face dice `license: unknown` y la página oficial no la indica en su texto | **CC BY-SA 4.0**, citada en la página oficial de VGG (verificada); los derechos de cada foto siguen en sus autores |
| Peso útil en el repo | ≈ 37 MB sin comprimir (12 000 × 3 072 B, cálculo) | subconjunto de 1 920 JPEG: 8,7 MB (q80) o 12,4 MB (q90), medido |

Cita: Parkhi, Vedaldi, Zisserman, Jawahar, «Cats and Dogs», CVPR 2012 (el nombre de la publicación figura en la página oficial; no se ha revisado el PDF). CIFAR: Krizhevsky, «Learning Multiple Layers of Features from Tiny Images», 2009 (según la página oficial).

Advertencias sobre los datos: en Oxford-IIIT Pet las razas están repartidas entre train y test (no hay test por razas nuevas), así que la cifra mide «razas ya vistas».  Un test de 720 imágenes da un intervalo de unos ±2 puntos.

## 2. Red

Todos los tiempos: este equipo, proceso limitado a **2 procesadores lógicos** (afinidad) y 2 hilos de PyTorch/ONNX Runtime. No son 2 núcleos físicos garantizados ni un Codespace: referencia, no promesa. Selección de épocas, `C` y finalistas con la partición de validación; el test solo se informa. Bootstrap de 2 000 remuestreos del test, percentiles 2,5 y 97,5.

### 2.1 CIFAR-10 gato/perro (test n = 2 000)

| Modelo | Parámetros | Entrenar (s) | Val | **Test** (IC95) | Modelo guardado (MB) |
|---|---|---|---|---|---|
| Regresión logística sobre píxeles | 3 073 | 5,7 | 60,6 % | 57,9 % (55,7–60,1) | no guardado |
| MLP scikit-learn (256) sobre píxeles | 786 945 | 170 | 57,2 % | 57,4 % (55,2–59,5) | ≈ 6,3 (float64, cálculo) |
| CNN propia, 20 épocas | 140 002 | 566 | 85,7 % | **86,4 %** (84,8–88,0) | 0,58 (.pt), 0,56 (ONNX) |
| MobileNetV3-small + cabeza, entrada 64 | 928 162 (3,9 MB .pt) | 5,5 | 73,6 % | 74,0 % (72,0–76,1) | 3,88 (.pt), 3,73 (ONNX) |
| ídem, entrada 96 | | 8,4 | 81,5 % | 81,4 % (79,6–83,1) | |
| ídem, entrada 128 | | 13,4 | 83,6 % | **83,6 %** (82,0–85,2) | |

Una MLP de scikit-learn sobre los píxeles es casi azar (57 %): **descartada**. Las cifras de la CNN suben con las épocas pero fluctúan entre épocas (la validación bajó a 58 % en la 2.ª); se guarda la mejor época según validación.

### 2.2 Oxford-IIIT Pet gato/perro (test n = 720)

| Modelo | Entrenar (s) | Val | **Test** (IC95) | .pt (MB) |
|---|---|---|---|---|
| CNN propia a 64×64 (287 714 parámetros), 20 épocas | 713 | 88,3 % | 88,8 % (86,4–91,1) | 1,17 |
| MobileNetV3-small + cabeza, entrada 96 | 5,8 | 88,9 % | 87,2 % (84,7–89,6) | 3,88 |
| MobileNetV3-small + cabeza, entrada 128 | 6,3 | 93,3 % | **93,1 %** (91,1–94,9) | 3,88 |

Los intervalos de la CNN propia y de MobileNet a 128 se solapan un poco; no se hizo prueba pareada, así que la diferencia de 4 puntos es probable pero no demostrada.

### 2.3 Cuántas fotos hacen falta (cabeza sobre MobileNet a 128; `C` = 0,1 fijo; test de 720)

| Fotos por clase | 10 | 25 | 50 | 100 | 300 | 600 | 1 680 |
|---|---|---|---|---|---|---|---|
| Test | 77,8 % | 83,2 % | 89,0 % | 91,1 % | 92,8 % | 92,9 % | 93,9 % |
| Segundos (rasgos + cabeza) | 0,1 | 0,1 | 0,2 | 0,3 | 0,7 | 1,3 | 3,2 |

Con 100 fotos por clase ya se supera el 91 %: el extra puede llevar un subconjunto pequeño.

### 2.4 Desplazamiento de dominio: lo entrenado con CIFAR frente a fotos reales

Fotos del test de Oxford-IIIT Pet reducidas a 32×32 (n = 720): CNN propia de CIFAR **79,0 %** (76,0–81,9); MobileNet-128 de CIFAR 80,8 % (77,9–83,5); a 64 y 96: 71,9 % y 77,5 %. Es decir, una persona que suba su foto a un modelo de CIFAR obtendrá algo claramente peor que el 86 % del test de CIFAR.

### 2.5 Tiempo de inferencia por imagen (2 hilos, lote de 1, mediana)

| Modelo | ONNX Runtime | `mlflow.pyfunc` | PyTorch en memoria |
|---|---|---|---|
| CNN propia CIFAR 32×32 | 0,60 ms | 0,50 ms | 2,0 ms |
| MobileNet-128 CIFAR (entrada 32) | 0,85 ms | 0,91 ms | 4,6 ms |
| MobileNet-128 fotos (entrada 128) | 0,61 ms | 0,77 ms | 3,6 ms |

Foto real de 150 KB (375×500) de extremo a extremo con el modelo que recibe bytes (decodificar, recortar, reducir, predecir): **3,9–4,6 ms**. Con la API de FastAPI y el cliente de pruebas (sin red real): mediana 52 ms (foto de 150 KB) y 73 ms (imagen ya del tamaño del modelo), p95 ≈ 110–130 ms. Esa latencia está dominada por el cliente de pruebas y el análisis del formulario multipart, no por el modelo.

### 2.6 Elección

La transferencia gana en lo que importa para una demo en vivo: se «entrena» en segundos, el resultado es bueno con fotos reales y pesa 3,7 MB. La CNN propia es más pequeña (0,6–1,2 MB) y didáctica, pero con 2 hilos tarda 9–12 minutos y, en fotos, no mejora a la transferencia. Un aviso conceptual para el instructor: ImageNet contiene muchas clases de perros y gatos, así que la red preentrenada ya «sabe» de qué va el problema; hay que contarlo como transferencia, no como «aprende de cero con 2 000 fotos». La licencia de los pesos preentrenados de torchvision **no se ha verificado**.

## 3. Biblioteca

En este equipo: `env-ia-opcional` **no existe**; `env-ia-mlops` tiene `mlflow` 3.18.0, `mlflow-skinny` 3.18.0, `numpy` 2.4.6, `pillow` 13.0.0 y `scikit-learn` 1.9.1, **sin PyTorch, ONNX ni ONNX Runtime**. No se instaló nada ahí: los entrenamientos se hicieron en un venv temporal (Python 3.11.18 como el del curso; PyTorch 2.15.0 CPU, torchvision 0.29.2, ONNX 1.23.2, ONNX Runtime 1.32.0, MLflow 3.18.0, pandas 2.3.3), ya borrado.

Tamaños medidos con `pip download` para **Linux x86_64 y Python 3.11** (la plataforma de `python:3.11-slim`), con las mismas versiones de `requirements-api.lock` más `pillow` y `python-multipart`. «Descomprimido» es la suma de los ficheros de las ruedas.

| Opción | Paquetes | Ruedas (MB) | Instalado descomprimido (MB) | Mayores (descomprimido) |
|---|---|---|---|---|
| A. **ONNX Runtime** | 51 | 83,2 | **263,5** | onnxruntime 75,7; numpy 57,4; pandas 43,6; pillow 20,4 |
| B. **PyTorch CPU** | 58 | 275,3 | **981,5** | torch 752,5 (rueda 209,5); numpy 57,4; pandas 43,6; sympy 26,8 |
| C. scikit-learn (como la API actual) | 54 | 100,9 | 336,6 | scipy 114,3; numpy 57,4; pandas 43,6; scikit-learn 31,5 |

La opción C coincide con el número de paquetes de `requirements-api.lock` (54), y es la que hoy pesa la imagen de S2. En un venv limpio de Windows con la opción A: 331 MB en total, incluidos `pip` (14 MB) y `setuptools` (9 MB); PyTorch no se carga (`torch_cargado: false`).

**Imagen Docker (estimado, no hay Docker en este equipo):** `python:3.11-slim` amd64 pesa 45,6 MB comprimida (Docker Hub, consulta del día). Descarga comprimida ≈ 45,6 + 83,2 ≈ **129 MB** (A) frente a ≈ 45,6 + 275,3 ≈ **321 MB** (B). En disco, la suma de A es 264 MB de paquetes más el sistema base (no medido) y la de B 982 MB más el base. El modelo añade 3,7–6,5 MB. La opción A es la de peso más bajo y no necesita cambiar el Dockerfile salvo el fichero de requisitos y la copia de la carpeta del modelo.

Tiempos de arranque (este equipo): `import torch` 1,7 s; `import mlflow.pyfunc` 1,7 s; `onnxruntime` 0,1 s; cargar el modelo en un proceso limpio 0,6–2,3 s.

## 4. MLflow

Se exportó cada finalista a ONNX (exportador clásico de PyTorch, opset 17; el paso de reducción y el softmax van dentro del grafo), se registró con `mlflow.onnx.log_model` con registro de modelo (SQLite, como el curso) y se guardó también con `mlflow.onnx.save_model` (carpeta lista para copiar a la imagen).

**Firma:** entrada `Tensor('uint8', (-1, H, W, 3))` llamada `imagen`; salida `Tensor('float32', (-1, 2))` llamada `probabilidades` (orden: gato, perro). H = 32 (CIFAR) o 128 (fotos). La API lee el lado desde la firma (`model.metadata.signature`).

**Entradas inválidas con `pyfunc`** (la firma sí protege): `float32` en lugar de `uint8`, forma sin canal, lado distinto (+1 píxel) y una imagen sin dimensión de lote fallan con `MlflowException: Failed to enforce schema`.

**Cosas que sorprenden** (medidas):
- El sabor `onnx` de `pyfunc` devuelve un **diccionario** `{ 'probabilidades': arreglo }`, no un arreglo ni un DataFrame. La API y las pruebas lo tratan.
- `mlflow.pyfunc` importa `pandas` y `mlflow-skinny` no lo declara: en un venv sin pandas falla con `ModuleNotFoundError: No module named 'pandas'`. Hay que ponerlo en los requisitos (ya está en `requirements-api.lock`).
- Por defecto declara `CUDAExecutionProvider` y avisa en el registro; se evita con `onnx_execution_providers=['CPUExecutionProvider']`.
- `input_example` con 2 imágenes de 128×128 añade unos 2,5 MB a la carpeta (6,5 MB frente a 3,9 MB): usar un solo ejemplo o ninguno.
- Opción de bytes: un `PythonModel` propio (`modelo_bytes.py`) con entrada `ColSpec('binary')` y el mismo preprocesado funciona y se carga en el venv limpio; necesita `code_paths` para `comun.py` y `pillow`.
- Aviso inocuo del exportador: «Converting a tensor to a Python boolean» (la comprobación del tamaño de entrada queda fija en el grafo; es lo que se quiere porque la firma fija H×W).

## 5. Pruebas: predice igual por todos los caminos

Comparación con la probabilidad de PyTorch sobre **todo** el test (diferencia máxima absoluta de probabilidad / predicciones con etiqueta distinta):

| Camino | CNN CIFAR (2 000) | MobileNet CIFAR (2 000) | MobileNet fotos (720) |
|---|---|---|---|
| ONNX Runtime directo | 6,6e-7 / 0 | 1,0e-5 / 0 | 1,2e-5 / 0 |
| `mlflow.pyfunc` (carpeta, MLflow completo) | 6,6e-7 / 0 | 1,0e-5 / 0 | 1,2e-5 / 0 |
| `mlflow.pyfunc` (`models:/` del registro) | 6,6e-7 / 0 | 1,0e-5 / 0 | 1,2e-5 / 0 |
| `mlflow.pyfunc` en venv limpio con `mlflow-skinny` | 6,6e-7 / 0 | 1,0e-5 / 0 | 1,2e-5 / 0 |
| Modelo de bytes con PNG (primeras 600) | 4,8e-7 / 0 | 5,8e-6 / 0 | 1,2e-5 / 0 |
| Modelo de bytes con PNG en venv limpio | 4,8e-7 | 5,8e-6 | 1,2e-5 |
| API con subida de PNG (50 imágenes, respuesta redondeada a 4 decimales) frente al camino directo | 4,9e-5 / - | - | 4,9e-5 / - |

La diferencia es la propia de float32 entre dos motores; nunca cambia una etiqueta.

**Lo que sí cambia la predicción: la compresión JPEG** (600 primeras imágenes del test, etiquetas distintas respecto a PNG sin pérdida):

| Calidad JPEG | CNN CIFAR 32×32 | MobileNet CIFAR 32×32 | MobileNet fotos 128×128 |
|---|---|---|---|
| 95 | 31 de 600 | 25 de 600 | 10 de 600 |
| 85 | 44 | 47 | 13 |
| 70 | 54 | 75 | 19 |

Con 32×32, subir una miniatura en JPEG cambia la etiqueta en 4–12 % de los casos; con 128×128, en 2–3 %. La exactitud de las fotos casi no baja (93,0 / 93,5 / 92,5 % frente a 93,7 % en PNG, mismas 600 filas).

## 6. Entrada de imágenes en una API (`api_demo.py`, `pruebas_api.py`)

Probada con el cliente de pruebas de FastAPI sobre el modelo de fotos (MobileNet-128) y sobre la CNN de CIFAR; los códigos HTTP fueron idénticos en ambos. Resultados:

| Caso | Resultado |
|---|---|
| PNG, JPEG, RGBA, gris, paleta, JPEG CMYK, foto real 375×500, JPEG de 12 MP | 200 |
| JPEG con orientación EXIF 6 | 200; se aplica la orientación (0,258/0,742 frente a 0,300/0,700 del mismo JPEG ya girado) |
| Archivo de texto con nombre `.jpg` | 415 |
| Vacío | 400 |
| 2,5 MB de ruido PNG (límite 2 MB) | 413 |
| JPEG truncado a la mitad | 422 |
| GIF, WebP (no admitidos) | 415 |
| Imagen de 8×8 (mínimo 16 px) | 422 |
| PNG de 12 000×12 000 que ocupa 136 KB (bomba de descompresión; límite 25 megapíxeles) | 413 |
| Falta el campo `archivo` | 422 |

Decisiones y límites:
- **Tamaño máximo:** se leen como mucho `MAX_BYTES + 1` bytes (2 MB). Según el funcionamiento de Starlette (no medido aquí), el cuerpo multipart se recibe entero antes de llamar a la función: el límite real de tamaño debe fijarse también en el proxy o en el servicio (el límite propio de Cloud Run no se ha verificado aquí).
- **Formato:** se decide por los bytes (Pillow lo identifica), no por el nombre ni el `Content-Type`.
- **Preprocesado:** recorte centrado a cuadrado y reducción LANCZOS al lado de la firma; es el **mismo código** (`preparar_imagen`) para entrenar y para servir. Cambiarlo en un sitio y no en otro es el fallo más probable de una demo.
- **Bombas de descompresión:** se comprueba ancho × alto antes de decodificar.
- Las imágenes no se guardan en disco ni se registran.

## 7. Esquema del extra y tiempo en vivo

Estructura propuesta (todo en `05-Extra-Red-Neuronal/`, fuera del proyecto base):

| Pieza | Contenido |
|---|---|
| `datos/` | 1 920 JPEG de 128×128 (≈ 9–12 MB), `LICENCIA.md` con la atribución CC BY-SA 4.0 y el aviso de derechos de los autores |
| `entrenar.py` | lee los JPEG, extrae rasgos con MobileNetV3-small, ajusta la cabeza, exporta a ONNX y registra en MLflow con firma (lo que hace `etapa_vivo.py`) |
| `requirements-api.txt` (variante ONNX) | los del lock + `onnxruntime` + `pillow` + `python-multipart`, **sin** scikit-learn ni scipy |
| `Dockerfile` | el de S2 con otro lock y la carpeta `modelo_mlflow/` (3,7 MB + 0,1 MB de metadatos) |
| `api.py` | `api_demo.py`: `POST /predecir` con subida de archivo y límites |
| Diapositivas (3) | 1) «Una red aprende de dos clases»: qué es transferencia (lo congelado frente a la cabeza). 2) «Es un modelo más»: firma de la imagen, registro en MLflow, qué cambia respecto al modelo tabular. 3) «Qué cambia al servir imágenes»: límites, formato, bomba, orden EXIF, y la tabla de pesos de la imagen |

**Tiempo en vivo, medido** (600 fotos por clase, 2 hilos, proceso ya con las bibliotecas importadas): leer 1 200 JPEG 0,5 s; rasgos 1,0 s; cabeza 0,0 s; exportar a ONNX 0,3 s; registrar en MLflow con firma 5,7 s; cargar `pyfunc` y predecir 0,1 s; **total 7,6 s**, exactitud en test 93,3 % (91,4–95,0). A eso hay que sumar el arranque del intérprete y la importación (`torch` 1,7 s, `mlflow` 1,7 s) y la descarga de los pesos de MobileNet (10,3 MB) la primera vez. **Estimación para la sesión (no medida en Codespace): 1–2 min de cómputo; reservar 10 min para explicarlo y 10 para construir la imagen y probar la API.**

**Recomendación:** entrenar en directo solo la cabeza (8–10 s) y tener el modelo ya registrado como respaldo. No entrenar la CNN propia en directo: 9–12 minutos con 2 hilos en este equipo y ruido entre épocas.

## 8. Riesgos y lo que no se pudo medir

| Riesgo | Detalle |
|---|---|
| Peso de la imagen | Con PyTorch: ≈ 982 MB de paquetes (321 MB comprimida estimada). Con ONNX Runtime: 264 MB (129 MB). Elegir ONNX Runtime |
| Tiempo en el Codespace | Las cifras son de un portátil con 14 hilos lógicos limitados a 2; un Codespace de 2 núcleos puede ir más lento. La CNN propia es el riesgo; la transferencia deja margen (unos 8 s frente a 30 min) |
| Instalar PyTorch en el Codespace | La rueda CPU de Linux pesa 209,5 MB comprimida (752,5 MB descomprimida); el tiempo de instalación no se midió. Conviene dejarlo preinstalado en `postCreateCommand` del contenedor de desarrollo o usar el modelo ya registrado |
| Licencias | CIFAR-10: licencia no declarada. Oxford-IIIT Pet: CC BY-SA 4.0 (hay que citar y compartir igual lo que se redistribuya). Pesos de torchvision: no verificado. Fotos propias del instructor: sin riesgo si las aporta él |
| CIFAR 32×32 como demo | Con fotos reales reducidas a 32×32 el acierto cae a 79–81 % y con JPEG sube el cambio de etiqueta; además se ven 32 píxeles, y una demo con errores visibles resta |
| Exactitud | 93 % no es perfecta: con 720 fotos de test, ±2 puntos; razas conocidas; fallan algunas fotos. El instructor debe decir que 93 % significa que 7 de cada 100 fallan |
| Entrada en la API | Ver sección 6; el límite de tamaño debe ponerse también fuera de la aplicación |
| Dependencias ocultas | `pandas` para `mlflow.pyfunc`; el sabor `onnx` devuelve un diccionario; `input_example` grande |

**No se pudo medir:**
- Construir y ejecutar la imagen Docker (no hay Docker): los tamaños de la imagen son estimados a partir de las ruedas de Linux y de la etiqueta comprimida del base.
- Ejecución en un Codespace real de 2 núcleos y 8 GB; la restricción a 2 procesadores lógicos es una aproximación.
- Instalación y entrenamiento con PyTorch en Linux; solo se descargaron las ruedas de Linux para medir su tamaño.
- Entrada de 224×224 o ajuste fino de las últimas capas de MobileNet (podría subir del 93 %); y una prueba pareada entre CNN propia y transferencia.
- Servidor real con `uvicorn` y varias peticiones simultáneas; la latencia de la API se midió con el cliente de pruebas.
- Descargas desde dentro del Codespace (red, Hugging Face, descarga de pesos).
- Licencia de los pesos preentrenados y el texto del PDF de la publicación de Oxford-IIIT Pet.

## Reproducir

En un venv temporal con Python 3.11 (`pip install numpy pillow scikit-learn pandas==2.3.3 pyarrow mlflow==3.18.0 onnx onnxruntime fastapi python-multipart httpx` más `torch` y `torchvision` del índice CPU de PyTorch), desde esta carpeta: `python pico.py datos`, `modelos`, `paquetes`, `mlflow --limpio <python de un venv con requirements-api.lock sin scikit-learn, scipy, joblib y threadpoolctl, más onnxruntime y pillow>`, `api`, `vivo`. `datos` descarga unos 1,0 GB (Oxford-IIIT Pet y CIFAR-10) a `_trabajo/`. Semilla 42 en todo; el orden de las épocas de la CNN puede variar algo entre versiones de PyTorch.

