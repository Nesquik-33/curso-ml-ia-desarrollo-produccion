# S3 · Laboratorio-recap de S2: la API, las variables de FS al vuelo y la interfaz

**Duración:** 90 minutos, de 0:10 a 1:40 de la sesión (10:10–11:40, hora de Perú). **Dónde:** en tu Codespace del curso. **GCP no entra hoy.**
**En clase se proyecta** [`index.html`](index.html) (20 diapositivas, cada orden con su botón ⧉ para copiarla). Esta guía es **el mismo recorrido en texto**, para que puedas repetirlo solo, a tu ritmo.

Siglas: **API**, interfaz de programación (el modelo atiende peticiones HTTP con JSON); **HTTP**, protocolo de transferencia de hipertexto; **JSON**, notación de objetos de JavaScript (el formato de texto de las peticiones); **FS**, capa de variables (*feature store*): las 13 variables de cada cliente en una fecha de corte; **UI**, interfaz de usuario (la página de consulta); **SQL**, lenguaje de consulta estructurado.

> **De dónde salen las salidas.** Las salidas de «Qué debes ver» son **reales**: las de ejecutar estas mismas órdenes **en local** (Windows, entorno `env-ia-mlops`, 20/11/2026) con un operacional y un pipeline recién hechos desde la muestra. En el Codespace (Linux) cambian las rutas, las horas y el texto de algunos errores del sistema; **los números deben coincidir**. Las capturas de la presentación son de un Codespace del curso.

## La idea en un minuto
```text
  id de cliente ──► variables en la fecha de corte ──► API del modelo ──► probabilidad ──► regla de negocio ──► tramo + recomendación
  (la interfaz)     (el mismo SQL de la capa FS)      (/predecir/lote)                    (config.SEGMENTOS_RECOMPRA)
```
- La **API no sabe qué es un id**: pide las 13 variables del contrato. Así la imagen del modelo no lleva datos de clientes.
- La **persona no conoce las variables**: solo tiene el id.
- La **interfaz hace de puente**: calcula las variables con el mismo SQL de FS que al entrenar, llama a la API y aplica la regla de tramos.

## Cómo trabajar: tres terminales
| Terminal | Qué corre | Puerto |
|---|---|---|
| **T1** | la API del modelo (`uvicorn`) | 8080 |
| **T2** | la interfaz de consulta | 8090 |
| **T3** | las comprobaciones (`curl`, Python) | — |

Divide el terminal con **Ctrl+Shift+5** (o el icono ◫ del panel). En las tres: carpeta `04-Proyecto-Base` y entorno `env-ia-mlops` activado.

| Parte | Qué | Min |
|---|---|---|
| A | Preparar el Codespace (pasos 1) | 14 |
| B | Inferencia: API, contrato, una predicción, un lote y un 422 (pasos 2 a 7) | 29 |
| C | Las variables de FS, calculadas al vuelo (paso 8) | 17 |
| D | La interfaz: 13599, variables, ejemplo, corte, vivo y listo (pasos 9 a 13) | 25 |
| E | Opcional con Docker y cierre | 5 |

---

## A · Preparar

### Paso 1 · Datos y modelo (solo en un Codespace nuevo)
**Orden** (T1). Si el terminal no está ya en la carpeta o sin el entorno:
```bash
cd /workspaces/curso-ml-ia-desarrollo-produccion/04-Proyecto-Base
conda activate env-ia-mlops
pwd && python --version && ls
```
Después, la base operacional y el pipeline (unos 2 minutos):
```bash
python -m ia_mlops.operacional && python -m ia_mlops.pipeline
```
**Qué debes ver** (salida en local, resumida):
```text
  OPERACIONAL: clientes               150 filas
  OPERACIONAL: productos            3,080 filas
  OPERACIONAL: facturas             1,430 filas
  OPERACIONAL: lineas_factura      23,070 filas
[pipeline_ingesta_raw] ejecutando (huella de entrada a3e0551c3461)
[pipeline_ingesta_master] ejecutando (huella de entrada d31efa33ae66)
[pipeline_ml] ejecutando (huella de entrada 16577f644dbe)
  FS: corte 2010-06-01: 69 clientes
  …
  FS: corte 2011-09-01: 131 clientes
  ML: train     626 filas | tasa de recompra 50.8 %
  ML: valid     114 filas | tasa de recompra 45.6 %
  ML: test      250 filas | tasa de recompra 40.4 %
[pipeline_train] ejecutando (huella de entrada 7108eeb2fa32)
  referencia_sin_aprender    AUC valid 0.500 | test 0.500 | precision media test 0.404
  regresion_logistica        AUC valid 0.698 | test 0.747 | precision media test 0.659
  gradient_boosting          AUC valid 0.663 | test 0.735 | precision media test 0.648
Successfully registered model 'retencion-90d'.
  Mejor modelo: regresion_logistica. Guardado en …/models/modelo.joblib
  Registrado en MLflow como «retencion-90d», version 1. Para verlo: python -m ia_mlops.mlflow_ui
```
Capturas: `img/r01-codespace.webp` y `img/r02-pipeline.webp`.

**Si falla**
- Los `UserWarning` y `WARNING mlflow.sklearn` **no son errores**.
- `conda: command not found` o el entorno no existe: el Codespace no se creó con el `devcontainer` del curso; crea otro desde la rama `develop`.
- Si ya lo tenías de S2, cada paso dice «sin cambios» y termina enseguida: también vale.

---

## B · Inferencia con la API

### Paso 2 · Arrancar la API (T1)
```bash
python -m uvicorn ia_mlops.api.app:app --host 127.0.0.1 --port 8080
```
**Qué debes ver** (salida en local): el terminal se queda ocupado escuchando.
```text
INFO:     Waiting for application startup.
{"severity": "INFO", "message": "modelo cargado", "evento": "modelo_cargado", "huella_datos": "35a94deb4e04ab4a"}
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```
En la pestaña **Puertos** aparece el **8080** («API ia-mlops (S2)»). Capturas: `img/r03-api-arrancada.webp` y `img/r04-puertos.webp`.

**Si falla**
- `address already in use`: el 8080 está ocupado (¿un contenedor de S2?). Míralo con `docker ps` y bórralo con `docker rm -f <nombre>`.
- La línea JSON dice `modelo no cargado`: falta `models/`; vuelve al paso 1.

### Paso 3 · Vivo, listo y qué modelo es (T3)
```bash
curl -s http://127.0.0.1:8080/salud; echo
curl -s http://127.0.0.1:8080/listo; echo
curl -s http://127.0.0.1:8080/modelo | python -m json.tool | head -n 25
```
**Qué debes ver** (salida en local; de `/modelo`, las primeras líneas):
```text
{"estado":"ok"}
{"estado":"listo"}
{
    "modelo": "regresion_logistica",
    "objetivo": "el cliente compra al menos una vez en los siguientes 90 dias",
    "huella_datos": "35a94deb4e04ab4a",
    "entrenado_en": "2026-11-20T12:22:53",
    "variables": [
        "recencia_dias",
        … (las 13 variables del contrato) …
        "es_reino_unido"
    ],
    "filas": {
        "train": 626,
        "valid": 114,
        "test": 250
    },
```
Más abajo (fuera de las 25 líneas de `head`) vienen `metricas_valid` (AUC de validación 0,698) y las versiones de Python y de las bibliotecas.
- **/salud**: ¿responde el proceso? (vivo). **/listo**: ¿tiene el modelo cargado? (listo). **/modelo**: qué modelo es y con qué datos se entrenó (`huella_datos`).
- La huella puede ser otra si tus datos son otros: compárala con la línea `modelo cargado` de T1.

### Paso 4 · El contrato en el navegador: /docs
- Pestaña **Puertos** → fila **8080** → icono del globo («Abrir en el navegador») → añade `/docs` a la dirección.
- Despliega **POST /predecir** → **Try it out** → **Execute**: el ejemplo trae las 13 variables.
- En **Schemas**, `Cliente`: los 13 campos con su tipo. Es el **contrato**, que sale de la firma del modelo.

Captura: `img/r05-docs.webp`.

### Paso 5 · Una predicción (T3)
```bash
curl -s -X POST http://127.0.0.1:8080/predecir -H "Content-Type: application/json" -d @tests/datos/cliente_ejemplo.json; echo
```
`-d @archivo` envía el archivo tal cual: `tests/datos/cliente_ejemplo.json` lleva las 13 variables (recencia 35 días, 6 compras, 1250,40 £…).

**Qué debes ver** (salida en local):
```text
{"probabilidad":0.8278889191932138,"modelo":"regresion_logistica","huella_datos":"35a94deb4e04ab4a","advertencias":[]}
```
- ≈ **0,828**: el mismo valor que en S2 (`0.8278889…`). Las últimas cifras pueden variar (coma flotante); si cambia la segunda o la tercera, tienes otros datos u otro modelo.
- En T1 aparece una línea JSON `POST /predecir 200` con su `id` y los milisegundos, **sin datos del cliente**.

Captura: `img/r06-predecir.webp`.

### Paso 6 · Un lote (T3)
```bash
curl -s -X POST http://127.0.0.1:8080/predecir/lote -H "Content-Type: application/json" -d @tests/datos/lote_ejemplo.json; echo
```
**Qué debes ver** (salida en local, recortada):
```text
{"predicciones":[
 {"probabilidad":0.8278889191932137, … ,"advertencias":[]},
 {"probabilidad":0.3061291959896073, … ,"advertencias":["dias_medios_entre_compras no informado: el modelo usa la mediana del entrenamiento."]}]}
```
- Dos predicciones, **en el mismo orden** que los clientes del archivo; hasta 1000 por petición.
- El segundo cliente tiene `dias_medios_entre_compras: null` (una sola compra): la API **avisa**, no rechaza.

Captura: `img/r07-lote.webp`.

### Paso 7 · Romper el contrato: 422 (T3)
```bash
curl -s -w ' [%{http_code}]\n' -X POST http://127.0.0.1:8080/predecir -H "Content-Type: application/json" -d '{"recencia_dias": 35}'
```
**Qué debes ver** (salida en local, recortada): la lista de las **12 variables que faltan** y el código 422.
```text
{"detail":[{"type":"missing","loc":["body","frecuencia"],"msg":"Field required", …}, … 12 campos que faltan …]} [422]
```
Repaso de códigos: **200** bien · **422** el cuerpo no cumple el contrato (culpa de quien llama) · **503** ahora no puedo (sin modelo, y dice por qué) · **500** error interno, sin detalles.

---

## C · Las variables de FS, calculadas al vuelo

### La idea
- La tabla `fs_cliente_corte` guarda las variables de cada cliente en los **10 cortes** de entrenamiento, validación y prueba (de 2010-06-01 a 2011-09-01).
- La campaña es **hoy** del dato: el día siguiente a la última factura, `2011-12-10`. Ese corte **no está guardado**.
- `ia_mlops.explotacion.variables_en_corte(con, corte)` lo calcula en el momento: ejecuta **el mismo SQL** de la capa FS (`sql/fs/02_poblar_fs.sql`) sobre una tabla **temporal** (la capa FS no se toca) y solo usa datos **anteriores al corte** (`fecha_factura < :corte`). Es lo que usan la interfaz y `python -m ia_mlops.explotacion`.

### Paso 8 · El fragmento (T3; no necesita la API)
Pega **la orden entera**, desde `python` hasta `EOF` (python lee el programa hasta esa línea):
```bash
python - <<'EOF'
import pandas as pd
from ia_mlops import config, db, explotacion as ex
con = db.conectar(); cid = 13599; t = {}
for corte in ['2010-12-01', ex.corte_por_defecto(con)]:
    v = ex.variables_en_corte(con, corte)
    t[f'al vuelo {corte}'] = v.loc[v.cliente_id == cid, config.FEATURES].iloc[0]
fs = pd.read_sql("SELECT * FROM fs_cliente_corte WHERE cliente_id = ? AND fecha_corte = '2010-12-01'", con, params=[cid])
t['tabla fs 2010-12-01'] = fs[config.FEATURES].iloc[0]
t = pd.DataFrame(t); print(t.to_string())
a, b = t.iloc[:, 0], t.iloc[:, 2]
print('Iguales en el corte entrenado:', bool(((a == b) | (a.isna() & b.isna())).all()))
print('Cortes guardados en fs_cliente_corte:', [r[0] for r in con.execute('SELECT DISTINCT fecha_corte FROM fs_cliente_corte ORDER BY 1')])
EOF
```
Qué hace: calcula al vuelo las 13 variables del cliente 13599 en dos cortes (el último de entrenamiento, `2010-12-01`, y el de hoy, `ex.corte_por_defecto`), lee la fila guardada en la tabla FS para el corte entrenado y compara.

**Qué debes ver** (salida en local):
```text
                           al vuelo 2010-12-01  al vuelo 2011-12-10  tabla fs 2010-12-01
recencia_dias                            21.00                 1.00                21.00
frecuencia                               12.00                33.00                12.00
monto_total                            4661.12              9811.04              4661.12
ticket_medio                            388.43               297.30               388.43
unidades_total                         2955.00              6248.00              2955.00
productos_distintos                     100.00               235.00               100.00
antiguedad_dias                         364.00               738.00               364.00
frecuencia_90d                            6.00                13.00                 6.00
monto_90d                              1752.00              2836.08              1752.00
frecuencia_180d                           6.00                14.00                 6.00
dias_medios_entre_compras                31.20                23.00                31.20
devoluciones                              7.00                19.00                 7.00
es_reino_unido                            1.00                 1.00                 1.00
Iguales en el corte entrenado: True
Cortes guardados en fs_cliente_corte: ['2010-06-01', '2010-07-01', '2010-08-01', '2010-09-01', '2010-10-01', '2010-11-01', '2010-12-01', '2011-03-01', '2011-06-01', '2011-09-01']
```
- Columnas 1 y 3 **iguales**: el cálculo al vuelo es el mismo que el que se guardó al entrenar.
- Hoy el 13599 tiene 33 compras y **738 días** de antigüedad; el modelo solo vio de **1 a 364**. Lo verás en la interfaz como «revisar» (deriva, S5).
- `2011-12-10` no está entre los cortes guardados: por eso se calcula al vuelo.

Captura: `img/r08-fs-al-vuelo.webp`.

**Si falla**
- `No existe la capa FS: ejecuta antes python -m ia_mlops.pipeline`: vuelve al paso 1.
- `ModuleNotFoundError: No module named 'ia_mlops'`: no estás en `04-Proyecto-Base`.
- El terminal se queda con `>` esperando: no se copió la última línea; escribe `EOF` y pulsa Intro.

**Para probar:** cambia `cid = 13599` por `18108` o el corte `'2010-12-01'` por `'2011-03-01'` (también está guardado: debe dar `True`).

---

## D · La interfaz de consulta

### Paso 9 · Arrancar la interfaz (T2, con la API en marcha en T1)
```bash
python -m ia_mlops.interfaz --url http://127.0.0.1:8080
```
**Qué debes ver** (salida en local):
```text
Interfaz en http://127.0.0.1:8090 · predicciones: http://127.0.0.1:8080
INFO:     Uvicorn running on http://127.0.0.1:8090 (Press CTRL+C to quit)
```
Compruébalo en T3:
```bash
curl -s http://127.0.0.1:8090/listo; echo
```
```text
{"estado":"listo","datos":"ok","modelo":"http://127.0.0.1:8080"}
```
Abre la página: pestaña **Puertos** → fila **8090** («Interfaz de consulta (S2)») → icono del globo. Debajo del formulario: «predicciones: http://127.0.0.1:8080».

**Si falla**
- `/listo` da 503 «no responde»: la API de T1 no está en marcha.
- No aparece el 8090 en Puertos: **Reenviar un puerto** y escribe `8090`.

### Paso 10 · Consultar el 13599 y ver sus variables
- Escribe `13599` en **Ids de cliente** y pulsa **Predecir**. La primera consulta tarda unos segundos: puntúa a los 148 clientes del corte.
- En su fila, despliega **Variables**.

**Qué debes ver** (salida en local, de `/recomendar/13599`):
```text
corte 2011-12-10 · 148 clientes en el corte
13599  probabilidad 0.9977  alta  puesto 1  decil 1  revisar
aviso: antiguedad_dias=738 esta fuera del rango visto al entrenar [1, 364]; la prediccion no tiene respaldo ahi.
```
- 99,8 %, tramo `alta`, puesto 1 de 148.
- Las variables son **las de la columna `2011-12-10` del paso 8**: recencia 1, frecuencia 33, monto 9811,04, antigüedad 738.

Capturas: `img/r09-interfaz-13599.webp` y `img/r10-interfaz-variables.webp`.

### Paso 11 · El botón Ejemplo
Pulsa **Ejemplo** (rellena cinco ids repartidos por el ranking y el `99999`) y después **Predecir**.

**Qué debes ver** (salida en local):
```text
13599  0.9977  alta   puesto 1
14859  0.7273  alta   puesto 38
18108  0.4159  media  puesto 75
14752  0.2249  baja   puesto 111
13306  0.128   baja   puesto 148
99999  no existe en MASTER
```
La regla de negocio (`config.SEGMENTOS_RECOMPRA`, no sale del modelo): **alta** desde 70 % (no gastar el incentivo) · **media** desde 40 % (prioridad de la campaña) · **baja** (contacto de bajo coste).

Captura: `img/r11-interfaz-ejemplo.webp`.

### Paso 12 · Cambiar la fecha de corte
**Limpiar**, escribe `13599`, pon **Fecha de corte** = 01/03/2011 y pulsa **Predecir**.

**Qué debes ver** (salida en local):
```text
corte 2011-03-01 · 114 clientes en el corte
13599  probabilidad 0.9942  alta  puesto 3
recencia_dias 53 · frecuencia 15 · monto_total 5383.1 · antiguedad_dias 454 · devoluciones 11
```
- Solo 114 clientes: los que habían comprado antes del 1/3/2011.
- Cambian las variables porque todas se calculan **con lo anterior al corte**.
- La fecha debe estar entre la primera factura y el día siguiente a la última; fuera de ese tramo, 422 con el motivo.

Captura: `img/r12-interfaz-corte.webp`.

### Paso 13 · Vivo frente a listo
En **T1**, **Ctrl+C** (se para la API). Después, en T3:
```bash
curl -s -w ' [%{http_code}]\n' http://127.0.0.1:8090/salud; curl -s -w ' [%{http_code}]\n' http://127.0.0.1:8090/listo
```
**Qué debes ver** (salida en local; en el Codespace el motivo es del tipo `[Errno 111] Connection refused`):
```text
{"estado":"ok"} [200]
{"detalle":"La API del modelo en http://127.0.0.1:8080 no responde ([WinError 10061] …). ¿Está arrancada y /listo responde?"} [503]
```
La interfaz está **viva** (200) pero **no lista** (503): reiniciarla no arregla nada, lo que falta es la API. Por eso el chequeo de salud de la imagen mira `/salud` y no `/listo`.

Captura: `img/r13-listo-503.webp`.

Al terminar: vuelve a arrancar la API en T1 si quieres seguir probando, o para las dos con **Ctrl+C**.

---

## E · Opcional: lo mismo en dos contenedores (Docker)
No se hace en clase. Es la **parte B** de la práctica de S2: [`01-Sesiones/S2-API-y-Docker/practica/interfaz-de-consulta.md`](../../S2-API-y-Docker/practica/interfaz-de-consulta.md), explicada en [`04-Proyecto-Base/docs/del-ordenador-al-servicio.md`](../../../04-Proyecto-Base/docs/del-ordenador-al-servicio.md).
- Antes, **para T1 y T2** (liberan el 8080 y el 8090).
- Todo de una vez, con Compose: `docker compose -f deploy/docker/compose.yaml up --build -d`, y al terminar `docker compose -f deploy/docker/compose.yaml down`.
- Qué cambia: la interfaz llama a `http://api:8080` (por nombre, en una red de Docker), los datos entran como volumen de **solo lectura** y la API no se publica (sin `-p`). **Los números deben ser los mismos.**

## Autoevaluación
1. **¿Por qué la API pide variables y no un id?** <details><summary>Respuesta</summary>Para que la imagen del modelo no lleve datos de clientes: el dato lo pone la interfaz.</details>
2. **¿Qué garantiza que las variables de hoy se calculen como las de entrenar?** <details><summary>Respuesta</summary>El mismo SQL de FS (`sql/fs/02_poblar_fs.sql`). En el corte entrenado, el cálculo al vuelo da los mismos valores que la tabla (`Iguales en el corte entrenado: True`).</details>
3. **¿Qué significa «revisar» en el 13599?** <details><summary>Respuesta</summary>Una variable (antigüedad 738 días) está fuera de lo visto al entrenar (1 a 364): la probabilidad no tiene respaldo ahí. Con el corte de hoy, 132 de los 148 clientes salen con advertencias (salida en local).</details>
4. **Con la API parada, ¿qué dan `/salud` y `/listo` de la interfaz?** <details><summary>Respuesta</summary>`/salud` 200 (viva) y `/listo` 503 con el motivo (no lista).</details>

## Qué se probó
- **En local (Windows, 20/11/2026):** todas las órdenes de los pasos 1 a 13, en ese orden, con un operacional y un pipeline nuevos en carpetas temporales (variables `CURSO_DB`, `CURSO_MODELOS`…, sin tocar los datos del proyecto). Las salidas de esta guía son esas. `curl` se lanzó con `curl.exe`; el 422 del paso 7 se obtuvo con la misma aplicación desde Python.
- **En el Codespace:** las capturas `img/r01…r13` de la presentación. Mientras falte alguna, la presentación muestra «Captura pendiente» en su lugar.
- **Sin probar hoy:** la parte E (Docker); se validó en S2 (GitHub Actions y Codespace, 14/11/2026).
- Pruebas de la presentación: `python -m pytest 01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-recap-s2/pruebas -q`.
