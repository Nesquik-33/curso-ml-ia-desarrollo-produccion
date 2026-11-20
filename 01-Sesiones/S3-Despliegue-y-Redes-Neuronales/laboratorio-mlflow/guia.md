# Laboratorio de MLflow (S3) · guía paso a paso

Mismo recorrido que la presentación `index.html` de esta carpeta, en texto, para repetirlo solo. Duración en clase: **45 minutos**.
Caso: Online Retail II, experimento y modelo registrado **`retencion-90d`**.

> Las salidas de terminal son **reales**: ejecución en local (Windows, entorno `env-ia-mlops`, MLflow 3.18.0, muestra del curso, en una carpeta
> temporal) el 20/11/2026, con las mismas órdenes. Las rutas se abrevian con `…`. Lo que se ve en la web de MLflow está en las capturas del
> Codespace del curso (`img/`); los textos de la web se describen «según la captura».
> Cada orden va en su bloque: en la presentación cada una tiene su botón **⧉** para copiarla.

---

## A. Qué es MLflow (7 min)

MLflow es el **cuaderno de laboratorio** del modelo. En el proyecto lo usa `ia_mlops/modeling/train.py` para dos cosas:

| Pieza | Pregunta que responde | Qué guarda el proyecto |
|---|---|---|
| **Seguimiento** (*tracking*) | ¿Qué probé y qué salió? | Experimento `retencion-90d`; una **ejecución** (*run*) por modelo (`referencia_sin_aprender`, `regresion_logistica`, `gradient_boosting`) y otra `MEJOR-<modelo>` para el elegido |
| **Registro** (*Model Registry*) | ¿Qué modelo uso y de dónde salió? | Modelo registrado `retencion-90d`: cada entrenamiento crea una **versión** nueva (1, 2, 3…), enlazada a su ejecución |

En cada ejecución:
- **Parámetros** (lo decidido antes de entrenar): `modelo`, `ventana_objetivo_dias`, `n_variables`, `huella_datos`. La ejecución `MEJOR-…` lleva solo `modelo` y `huella_datos`.
- **Métricas** (lo medido después): `<partición>_<métrica>` con partición `train`, `valid`, `test` y métrica `auc`, `precision_media`, `tasa_base`, `aciertos_en_el_10_mejor` (12 por ejecución).
- **Artefactos**: solo en `MEJOR-…`, el modelo con su **firma** (nombre y tipo de las 13 entradas y de la salida) y un ejemplo de entrada.
- En cada **versión** registrada, tres etiquetas: `modelo`, `huella_datos` y `valid_auc`.

## B. Dónde vive (4 min)

Todo está en `04-Proyecto-Base/models/`:
- `mlflow.db`: base SQLite con experimentos, ejecuciones, parámetros, métricas y el registro de modelos.
- `mlartifacts/`: los archivos. En MLflow 3, el modelo guardado está en `mlartifacts/models/m-<identificador>/artifacts/`.

No hay que crear nada aparte: lo crea el **primer entrenamiento** con MLflow (`python -m ia_mlops.pipeline`).

**Por qué `python -m ia_mlops.mlflow_ui` y no `mlflow ui` a pelo.** La orden `mlflow ui --backend-store-uri sqlite:///models/mlflow.db` usa una ruta
**relativa**: lanzada desde la raíz del repositorio (donde se abre el terminal), MLflow crea otra base **vacía** sin dar ningún error, y la web no
enseña nada. `ia_mlops/mlflow_ui.py` calcula la ruta **absoluta** (la misma en la que escribe `train.py`), comprueba que hay ejecuciones y solo
entonces arranca la web. La web lee la base en cada petición: tras entrenar basta con recargar (F5).

## C. Práctica en el Codespace (30 min)

Dos terminales: **T1** para la interfaz (se queda ocupado) y **T2** para el resto. Los dos, desde `04-Proyecto-Base` y con `env-ia-mlops`.

### Paso 1 · Comprobar el registro (T1)

```
cd /workspaces/curso-ml-ia-desarrollo-produccion/04-Proyecto-Base
```
```
conda activate env-ia-mlops
```
```
python -m ia_mlops.mlflow_ui --comprobar
```

**Qué debes ver** (captura `img/m01-comprobar.webp`):
```
Registro de MLflow: …/04-Proyecto-Base/models/mlflow.db
  Experimento «retencion-90d»: 4 ejecuciones · modelo registrado «retencion-90d»: 1 versiones
```
Cuatro ejecuciones = tres modelos + `MEJOR-regresion_logistica`. Si has entrenado más veces, verás más; es normal.

**Si falla.** Si sale esto, aún no has entrenado con MLflow:
```
  No existe todavía. Entrena primero:  python -m ia_mlops.pipeline   (o ejecuta el cuaderno 04 con USAR_MLFLOW = True)
```
Ejecuta `python -m ia_mlops.pipeline` y repite. `No module named ia_mlops`: no estás en `04-Proyecto-Base`.

### Paso 2 · Arrancar la interfaz (T1)

```
python -m ia_mlops.mlflow_ui
```

**Qué debes ver** (captura `img/m02-arrancar.webp`): primero las líneas de `mlflow_ui` y, debajo, los mensajes de arranque del servidor de MLflow.
```
Registro de MLflow: …/04-Proyecto-Base/models/mlflow.db
  Experimento «retencion-90d»: 4 ejecuciones · modelo registrado «retencion-90d»: 1 versiones
Abriendo http://127.0.0.1:5000  ·  En la web elige «Model training» (arriba a la izquierda).  ·  Para parar: Ctrl+C
```
Abre la web: pestaña **Puertos** → fila **5000** → icono del globo. Abre un **segundo terminal** (T2) para los pasos 9 y 11.

**Si falla.**
- Página en blanco: la primera carga tarda unos **10 s**. Espera y recarga con **F5**.
- Puerto ocupado: `python -m ia_mlops.mlflow_ui --port 5001` (y abre el 5001 en Puertos).
- La web dice **«Invalid Host header»** (no ha pasado en el Codespace del curso; plan B **sin verificar** allí): para con Ctrl+C y lanza
  ```
  python -m mlflow ui --backend-store-uri "$(python -c 'from ia_mlops import mlflow_ui; print(mlflow_ui.uri())')" --port 5000 --allowed-hosts '*' --cors-allowed-origins '*'
  ```

### Paso 3 · Elegir «Model training» (navegador)

Captura `img/m03-inicio.webp`. MLflow 3 abre en el modo **GenAI**. Arriba a la izquierda, en el conmutador **GenAI | Model training**, pulsa
**Model training**. El menú de la izquierda cambia (según la captura) y ahí están los experimentos y el registro de modelos.

**Si falla.** Menús de IA generativa (trazas, prompts…): sigues en GenAI. No hay ningún experimento: estás leyendo otra base; Ctrl+C en T1 y vuelve al paso 1.

### Paso 4 · El experimento (navegador)

Captura `img/m04-experimento.webp`. **Experiments** → `retencion-90d` (el experimento `Default` lo crea MLflow solo y está vacío).
Con **Columns** añade `valid_auc`, `test_auc` y `huella_datos`.

**Qué debes ver:** cuatro ejecuciones (`referencia_sin_aprender`, `regresion_logistica`, `gradient_boosting`, `MEJOR-regresion_logistica`), todas con
la misma `huella_datos` (`35a94deb4e04ab4a` con la muestra). La `MEJOR-…` es la que tiene el modelo registrado (según la captura).

### Paso 5 · Detalle de una ejecución (navegador)

Captura `img/m05-run-detalle.webp`. Clic en `regresion_logistica`.

**Qué debes ver:** parámetros `modelo`, `ventana_objetivo_dias` = 90, `n_variables` = 13, `huella_datos`; y las 12 métricas. Con la muestra,
`valid_auc` 0,698 y `test_auc` 0,747.
- `aciertos_en_el_10_mejor`: de los clientes con el 10 % de probabilidades más altas, cuántos compraron de verdad.
- `tasa_base`: la proporción de compradores; es el listón de `precision_media`.

### Paso 6 · Comparar ejecuciones (navegador)

Captura `img/m06-comparar.webp`. En la lista marca `regresion_logistica` y `gradient_boosting` y pulsa **Compare**.

Valores reales con la muestra (leídos de la base con `MlflowClient`):

| Ejecución | train_auc | valid_auc | test_auc | valid_precision_media |
|---|---|---|---|---|
| referencia_sin_aprender | 0,500 | 0,500 | 0,500 | 0,456 |
| regresion_logistica | 0,803 | **0,698** | 0,747 | 0,736 |
| gradient_boosting | 1,000 | 0,663 | 0,735 | 0,704 |

- El boosting saca 1,000 en train y 0,663 en valid: ha **memorizado** (sobreajuste).
- Gana la regresión logística por **más AUC en valid**. Test se informa, no se usa para elegir.

### Paso 7 · Artefactos y firma (navegador)

Captura `img/m07-artefactos.webp`. Abre `MEJOR-regresion_logistica` y, desde ella, el modelo `modelo` y sus artefactos (según la captura). En MLflow 3
el modelo no cuelga de la carpeta de la ejecución: tiene su propio identificador `m-…`; si la pestaña de artefactos de la ejecución sale vacía, es normal.

**Qué debes ver:**
- Archivos: `MLmodel`, `model.pkl`, `input_example.json`, `serving_input_example.json`, `conda.yaml`, `python_env.yaml`, `requirements.txt`.
- Firma: **13 entradas** (tipo `long` o `double`; `dias_medios_entre_compras` no es obligatoria) y **1 salida** `float64`, la probabilidad.
- En disco: `models/mlartifacts/models/m-<identificador>/artifacts/`.

### Paso 8 · El modelo registrado (navegador)

Captura `img/m08-modelos.webp`. Menú izquierdo: registro de modelos → `retencion-90d`.

**Qué debes ver:** una fila por versión (**Version 1**), con las etiquetas `modelo` = regresion_logistica, `huella_datos` y `valid_auc` = 0.6982.
Desde la versión se llega a la ejecución `MEJOR-…` de la que salió.

### Paso 9 · Reentrenar: versión 2 (T2)

Con la interfaz abierta en T1, en **T2**:
```
cd /workspaces/curso-ml-ia-desarrollo-produccion/04-Proyecto-Base
```
```
python -m ia_mlops.pipeline_train
```
**Qué debes ver:** no entrena, porque el pipeline es **idempotente** (mismos datos y mismo código):
```
[pipeline_train] sin cambios: la entrada es la misma que en la ultima ejecucion (7108eeb2fa32). Usa --forzar para rehacerlo.
```
Ahora con `--forzar`:
```
python -m ia_mlops.pipeline_train --forzar
```
**Qué debes ver** (captura `img/m09-forzar.webp`; entre medias salen avisos `UserWarning` y `WARNING` de MLflow y barras «Downloading artifacts», que son normales):
```
[pipeline_train] ejecutando (huella de entrada 7108eeb2fa32)
  referencia_sin_aprender    AUC valid 0.500 | test 0.500 | precision media test 0.404
  regresion_logistica        AUC valid 0.698 | test 0.747 | precision media test 0.659
  gradient_boosting          AUC valid 0.663 | test 0.735 | precision media test 0.648
Registered model 'retencion-90d' already exists. Creating a new version of this model...
Created version '2' of model 'retencion-90d'.
  Mejor modelo: regresion_logistica. Guardado en …/models/modelo.joblib
  Registrado en MLflow como «retencion-90d», version 2. Para verlo: python -m ia_mlops.mlflow_ui
```
Y la comprobación:
```
python -m ia_mlops.mlflow_ui --comprobar
```
```
Registro de MLflow: …/04-Proyecto-Base/models/mlflow.db
  Experimento «retencion-90d»: 8 ejecuciones · modelo registrado «retencion-90d»: 2 versiones
```
Los resultados son idénticos a los de la versión 1 (mismos datos, mismo código): lo nuevo es la versión, enlazada a su propia ejecución.

### Paso 10 · Versiones 1 y 2 (navegador)

Captura `img/m10-version2.webp`. Pulsa **F5** en `retencion-90d` (no hace falta reiniciar `mlflow_ui`).
**Qué debes ver:** Version 1 y Version 2, con las mismas etiquetas; en el experimento, 8 ejecuciones. La versión 1 no se borra.

### Paso 11 · Cargar el modelo registrado y predecir (T2)

Pega la orden **entera**, de `python` a `EOF`:
```
python - <<'EOF'
import json, warnings
warnings.filterwarnings('ignore')
import mlflow, mlflow.sklearn
import pandas as pd
from ia_mlops import config, mlflow_ui

mlflow.set_tracking_uri(mlflow_ui.uri())          # la base DEL PROYECTO, con ruta absoluta
nombre = config.MODELO_REGISTRADO                 # 'retencion-90d'
versiones = mlflow.MlflowClient().search_model_versions(f"name='{nombre}'")
ultima = max(int(v.version) for v in versiones)
print(f'Modelo registrado {nombre}: versiones {sorted(int(v.version) for v in versiones)}; cargo la {ultima}')

uri = f'models:/{nombre}/{ultima}'
firma = mlflow.models.get_model_info(uri).signature
print('Firma:', len(firma.inputs.inputs), 'entradas ->', firma.outputs.inputs[0].type)

modelo = mlflow.sklearn.load_model(uri)
cliente = json.load(open('tests/datos/cliente_ejemplo.json'))
fila = pd.DataFrame([cliente])[config.FEATURES]
print(f'Probabilidad de recompra en 90 días (cliente de ejemplo): {modelo.predict_proba(fila)[0, 1]:.3f}')
EOF
```
**Qué debes ver** (captura `img/m11-cargar.webp`):
```
Modelo registrado retencion-90d: versiones [1, 2]; cargo la 2
Firma: 13 entradas -> float64
Probabilidad de recompra en 90 días (cliente de ejemplo): 0.828
```
0,828 es la misma probabilidad que da la API de S2 para `tests/datos/cliente_ejemplo.json` (`0.8278889…`).

Por qué así:
- `set_tracking_uri(mlflow_ui.uri())`: la misma base, con ruta absoluta, que usa `train.py`.
- `models:/retencion-90d/2`: el modelo por **nombre y versión** del registro.
- `mlflow.sklearn.load_model` y `predict_proba`: con `mlflow.pyfunc.load_model(...).predict` saldría la clase (0 o 1), no la probabilidad.
- La API de S2 no lee el registro: carga la copia `models/modelo_mlflow`, que `train.py` exporta con la misma firma.

**Si falla.** Se queda con `>`: falta la última línea, `EOF`; escríbela y pulsa Intro. «Modelo no encontrado»: no estás usando la base del proyecto
(revisa que estás en `04-Proyecto-Base` y que usas `mlflow_ui.uri()`).

Al terminar: **Ctrl+C** en T1 para parar la interfaz.

## D. Cierre (4 min)

**Qué aporta en producción (S4 y S5).** Cada versión apunta a su ejecución (parámetros, métricas, huella de los datos): trazabilidad. A una versión
se le pone un **alias** (por ejemplo `produccion`) y el despliegue carga el alias; si la versión nueva falla, se mueve el alias a la anterior, sin
reentrenar ni borrar nada.

**Autoevaluación**
1. ¿Qué diferencia hay entre un parámetro y una métrica? — El parámetro se decide antes de entrenar; la métrica se mide después.
2. ¿Por qué `python -m ia_mlops.mlflow_ui` y no `mlflow ui` a pelo? — Calcula la ruta absoluta de `models/mlflow.db`; con la relativa, desde otra carpeta, MLflow crea una base vacía sin avisar.
3. ¿Por qué sin `--forzar` no se creó la versión 2? — El pipeline es idempotente: mismos datos y mismo código, «sin cambios».
4. ¿Qué es la firma y quién la usa? — El contrato de entrada y salida del modelo (13 entradas, 1 salida); la API la comprueba al arrancar.

## Si algo falla (resumen)

| Lo que ves | Qué haces |
|---|---|
| La web abre, pero no hay ejecuciones | Pulsa **Model training**; si sigue vacía, Ctrl+C y lanza desde `04-Proyecto-Base` `python -m ia_mlops.mlflow_ui` |
| Página en blanco al abrir el 5000 | Espera unos 10 s y pulsa F5 |
| Puerto 5000 ocupado | `python -m ia_mlops.mlflow_ui --port 5001` |
| Entrenas y no aparece nada nuevo | El pipeline dijo «sin cambios»: usa `--forzar`. Si entrenó, F5 |
| `No module named ia_mlops` / `No module named mlflow` | `cd 04-Proyecto-Base` / `conda activate env-ia-mlops` |
| Empezar de cero | Ctrl+C; `rm -rf models/mlflow.db models/mlartifacts` (los dos) y `python -m ia_mlops.pipeline` |

Más detalle: `01-Sesiones/recap/recap-01/mlflow-paso-a-paso.md`.
