# Laboratorio S3 · De local a GCP (guía replicable)

> **Material de preparación para S4: en la S3 del 20/11 GCP solo se explica; la práctica es en S4** (miércoles 25/11). La tarea de S3 no es esta migración: consulta la tarea de la sesión. Antes de S4 puedes adelantar el paso 0 (cuenta y proyecto de GCP listos, con presupuesto) y la ruta sin nube.

Esta guía sirve para **hacer la práctica de GCP en tu cuenta y con tu caso** (Bank Marketing), y para repetirla sin el instructor. Teoría y glosario: [`../teoria/README.md`](../teoria/README.md).

> **Estado a 20/11/2026: nada de esta guía se ha ejecutado en Google Cloud.** Cada paso lleva una marca:
> - **[REAL · local]**: ejecutado de verdad, en local; el «qué debes ver» es la salida guardada en [`ensayo-local/`](ensayo-local/).
> - **[REAL · mostrar]**: el script se ejecutó **sin opciones** (modo «mostrar»: imprime las órdenes y no ejecuta ninguna); la salida está en `ensayo-local/mostrar-*.txt`.
> - **[NUBE · sin verificar]**: la orden está en los scripts del repositorio, pero **no se ha ejecutado contra GCP**. El «qué debes ver» se deduce del código del script, no de una ejecución. Si lo que ves es distinto, **anótalo en tu evidencia** (es información valiosa, no un fallo tuyo).
>
> Los **tiempos** de cada paso son **estimaciones** para planificarte, no medidas. Los **costes**: consulta la consola de facturación y la página de precios de cada servicio; aquí no hay cifras.

## Antes de nada: dos rutas, las dos válidas

| Ruta | Para quién | Qué haces |
|---|---|---|
| **A · Con nube** | Tienes un proyecto de GCP con facturación activa **y** quieres usarlo | Todos los pasos |
| **B · Sin nube** | No tienes facturación o no quieres activarla | Pasos 1–4, 13 y 15, más el **plan escrito** del apartado B. **Nadie está obligado a pagar.** La rúbrica no penaliza no usar la nube si lo declaras; sí penaliza fingirla |

**Versión corta (mínimo de la ruta A):** pasos 0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11 (basta con `/listo` y una predicción), 14 y 15. El paso 12 y la comparación completa del paso 11 son deseables, no obligatorios.

## Dónde se ejecuta

- **En el Codespace del curso** (rama `develop`), en su terminal: es `bash` y trae Docker y el entorno `env-ia-mlops`. Todas las órdenes de esta guía son de `bash` y se lanzan **desde `04-Proyecto-Base`**, salvo que se diga otra cosa.
- **Plan B: Cloud Shell** (el terminal de Google Cloud en el navegador). Trae `gcloud`, pero **no** trae `env-ia-mlops` ni el repositorio: tendrías que traerlos (sin verificar).
- **No uses PowerShell ni CMD de Windows**: los scripts son de `bash` y su equivalente en Windows no se ha probado ni se documenta.
- Para el Codespace: arráncalo solo cuando vayas a trabajar y **páralo al terminar** (las horas son limitadas).

## Índice y tiempos (estimación)

| Paso | Qué | Ruta | Tiempo (estimación) | Marca |
|---|---|---|---|---|
| 0 | Proyecto, presupuesto y plan de limpieza escrito | A | 20 min | NUBE · sin verificar |
| 1 | Abrir el Codespace y el entorno | A y B | 10 min | REAL · local |
| 2 | Ver todos los scripts en modo «mostrar» | A y B | 10 min | REAL · mostrar |
| 3 | Inventario de tu caso | A y B | 15 min | REAL · local |
| 4 | Ensayo local de la migración (con rotura) | A y B | 25 min | REAL · local |
| 5 | SDK, sesión y `env.sh` | A | 15 min | NUBE · sin verificar |
| 6 | Comprobación previa, APIs y presupuesto | A | 15 min | NUBE · sin verificar |
| 7 | Datos: bucket, BigQuery y validación | A | 30 min | NUBE · sin verificar |
| 8 | Secreto y cuenta de servicio mínima | A | 15 min | NUBE · sin verificar |
| 9 | Medir la memoria y publicar la imagen | A | 30 min | NUBE · sin verificar |
| 10 | Cloud Run privado | A | 15 min | NUBE · sin verificar |
| 11 | Probar el servicio y leer sus registros | A | 25 min | NUBE · sin verificar |
| 12 | (Opcional) segunda revisión y vuelta atrás | A | 15 min | NUBE · sin verificar |
| 13 | Plan de rollback hacia lo local | A y B | 15 min | texto |
| 14 | Limpieza y listados vacíos | A | 20 min | NUBE · sin verificar |
| 15 | Evidencia de la práctica | A y B | 20 min | texto |
| B | Plan escrito de la migración (ruta sin nube) | B | 30 min | texto |

Total aproximado: ruta A, unas 5 h repartidas en dos o tres días; ruta B, unas 2 h. **Haz el paso 14 el mismo día en que crees recursos.**

En la S3 del viernes 20/11 estos pasos solo se explican; la práctica es en S4.

---

## 0. Proyecto, presupuesto y plan de limpieza (ruta A · 20 min · NUBE · sin verificar)

Esto va **antes** de crear cualquier recurso.

1. **Crea un proyecto nuevo y desechable** en la consola de Google Cloud, con un nombre genérico (sin tu nombre ni el de tu empresa). Apunta su **ID** solo en tu `env.sh` (paso 5), nunca en el repositorio.
2. **Vincula la facturación** al proyecto. Si no puedes o no quieres, **pasa a la ruta B**.
3. **Crea un presupuesto con alertas** con un importe pequeño que elijas tú. Puedes hacerlo en la consola (Facturación → Presupuestos y alertas) o con `preparar_proyecto.sh --ejecutar` (paso 6). **Una alerta avisa, no corta el gasto** (lo asume el curso; compruébalo en la documentación vigente).
4. **Escribe tu plan de limpieza antes de crear nada:** copia la lista del paso 14 en tu evidencia, con tus nombres. Si no sabes cómo vas a borrar algo, no lo crees.

**Qué debes ver:** el proyecto en la consola; el presupuesto en Facturación → Presupuestos y alertas.
**Si falla:** sin permiso para crear proyectos o sin cuenta de facturación → ruta B. **No uses el proyecto ni las credenciales de otra persona.**
**Coste:** crear el proyecto y el presupuesto no crea recursos; consulta la consola.

## 1. Abrir el Codespace y el entorno (rutas A y B · 10 min · REAL · local)

```bash
cd 04-Proyecto-Base
conda activate env-ia-mlops
python -m pytest -q tests/test_migracion.py
```

**Qué debes ver** (ejecutado en local el 20/11/2026): `44 passed`.
**Si falla:** `No module named ia_mlops.migracion` → no estás en `04-Proyecto-Base` o tu copia de `develop` no tiene aún el material de S3 (actualiza la rama). `Falta pyarrow` → no has activado `env-ia-mlops`.

## 2. Ver todos los scripts en modo «mostrar» (rutas A y B · 10 min · REAL · mostrar)

Sin opciones, **ningún script crea nada**: imprime las órdenes que ejecutaría. No hace falta `gcloud`, ni sesión, ni `env.sh`.

```bash
bash deploy/gcp/preparar_proyecto.sh
bash deploy/gcp/datos.sh
bash deploy/gcp/secretos_y_cuenta.sh
bash deploy/gcp/imagen.sh
bash deploy/cloud-run/desplegar.sh
bash deploy/cloud-run/probar.sh
```

**Qué debes ver:** cada uno empieza por `### MODO MOSTRAR: solo se imprimen las ordenes, NO se ejecuta nada. Para ejecutarlas anade --ejecutar.` y lista órdenes con marcadores `TU-PROYECTO` y `TU-REGION`. Las salidas reales están en [`mostrar-preparar_proyecto.txt`](ensayo-local/mostrar-preparar_proyecto.txt), [`mostrar-datos.txt`](ensayo-local/mostrar-datos.txt), [`mostrar-secretos_y_cuenta.txt`](ensayo-local/mostrar-secretos_y_cuenta.txt), [`mostrar-imagen.txt`](ensayo-local/mostrar-imagen.txt), [`mostrar-desplegar.txt`](ensayo-local/mostrar-desplegar.txt) y [`mostrar-probar.txt`](ensayo-local/mostrar-probar.txt). Por ejemplo, el despliegue:

```text
+ gcloud run deploy retencion-api --project TU-PROYECTO --region TU-REGION --image TU-REGION-docker.pkg.dev/TU-PROYECTO/curso-ml-imagenes/retencion-api:s3-1 --no-allow-unauthenticated --min-instances 0 --max-instances 2 --port 8080 --service-account sa-retencion-api@TU-PROYECTO.iam.gserviceaccount.com --set-secrets CURSO_DEMO_SECRETO=curso-ml-demo-secreto:1 --set-env-vars CURSO_LOG_NIVEL=INFO --labels=curso=ml-ia
```

Fíjate en lo que **no** aparece: ningún `allUsers`, ninguna etiqueta `latest`, ninguna clave JSON. Cada script explica en su cabecera qué crea, qué puede costar y cómo se borra: `bash deploy/gcp/datos.sh --ayuda`.
**Si falla:** `Opcion desconocida` → los scripts solo aceptan `--ejecutar` (crear de verdad), `--comprobar` (ejecuta solo las lecturas; necesita `gcloud`, sesión y `env.sh`) y `--ayuda`. `--confirmar` es de `limpiar.sh`, que aún no existe.

## 3. Inventario de tu caso (rutas A y B · 15 min · REAL · local)

Primero, con la base del curso, para ver qué esperar:

```bash
python -m ia_mlops.migracion inventario --db data/processed/curso.db
```

**Qué debes ver** (real, [`inventario.txt`](ensayo-local/inventario.txt)):

```text
Inventario de curso.db (7520256 bytes)
Tablas a migrar: 10 (29743 filas en total)
tabla                 capa        filas  cols  clave
fs_catalogo           fs_            13     5  feature
...
ml_particiones        ml_            10     4  fecha_corte
Tablas que NO se migran: 7
  control_pipelines            4 filas  (no empieza por un prefijo elegido)
  raw_carga                    4 filas  (no empieza por un prefijo elegido)
...
```

Después, **con tu base** (la SQLite que genera tu pipeline del avance 2; usa su ruta real):

```bash
python -m ia_mlops.migracion inventario --db RUTA/A/TU_BASE.db
python -m ia_mlops.migracion inventario --db RUTA/A/TU_BASE.db --json > inventario-mi-caso.json
```

Por defecto entran las tablas que empiezan por `master_`, `fs_` y `ml_` (en tu caso, por ejemplo, `master_llamadas`, `fs_llamada`, `ml_dataset`). Si tus nombres son otros: `--prefijos a_,b_` o `--tablas t1,t2`.

**Completa a mano** lo que la orden no detecta (no lee variables de entorno, secretos ni servicios): variables y secretos de tu API, imagen y puerto, dónde vive el modelo, si usas MLflow. Y decide la **estrategia por pieza** con el mapa de la teoría (apartado 4).
**Si falla:** `No hay tablas que empiecen por ...` → tus prefijos son otros (`--prefijos` o `--tablas`).

## 4. Ensayo local de la migración (rutas A y B · 25 min · REAL · local)

Exporta tus tablas a Parquet, comprueba la huella y valida contra la SQLite. **No es GCP**: todo ocurre en tu disco.

Con la base del curso (orden a orden; `CARPETA` es una carpeta temporal fuera del repositorio, por ejemplo `/tmp/s3-parquet`):

```bash
python -m ia_mlops.migracion exportar --db data/processed/curso.db --salida /tmp/s3-parquet
python -m ia_mlops.migracion huella verificar /tmp/s3-parquet
python -m ia_mlops.migracion validar --db data/processed/curso.db --destino /tmp/s3-parquet --json /tmp/s3-parquet/validacion.json
echo "codigo de salida: $?"
```

**Qué debes ver** (real, [`cli-exportar-validar.txt`](ensayo-local/cli-exportar-validar.txt) y [`validar.txt`](ensayo-local/validar.txt)):

```text
master_lineas            22117 filas     270390 bytes
...
TOTAL 29743 filas, 444856 bytes de Parquet, 1.801 s
coincide conteos.json: huella igual
...
RESULTADO: coincide (62 comprobaciones)
```

y código de salida `0`. Los bytes y las huellas se repiten entre ejecuciones; **los segundos no**. La carpeta queda con un `.parquet` por tabla, `esquema.json`, `conteos.json` y `MANIFEST.sha256`.

Después, **el ensayo completo con tu base**, que además hace una **rotura deliberada** (borra una fila de la tabla más grande y comprueba que `validar` lo detecta) y guarda todo:

```bash
python -m ia_mlops.migracion ensayo --db RUTA/A/TU_BASE.db --salida evidencia-s3/ensayo-local
```

**Qué debes ver** (real con la base del curso, [`validar-rotura.txt`](ensayo-local/validar-rotura.txt)): en `validar.txt`, `RESULTADO: coincide`; en `validar-rotura.txt`, líneas `DIFIERE` en `filas`, `agregados`, `muestra` y `huella` de la tabla rota y `RESULTADO: DIFIERE (4 de 62 comprobaciones fallan)` (con tu base, otros números). Guarda la carpeta para la evidencia. El ensayo usa solo `--prefijos` (no `--tablas`).

**Si falla:** `hay valores que no caben en ...` → una columna mezcla tipos en SQLite; revisa tu capa MASTER. `DIFIERE` en la copia fiel → no sigas: es justo lo que la validación debe parar.

## 5. SDK, sesión y `env.sh` (ruta A · 15 min · NUBE · sin verificar)

1. **SDK de Google Cloud en el Codespace** (guía completa: [`03-Entorno/guias/sdk-google-cloud-vscode-y-codespaces.md`](../../../03-Entorno/guias/sdk-google-cloud-vscode-y-codespaces.md)), desde la raíz del repositorio:
   ```bash
   bash 04-Proyecto-Base/deploy/gcp/instalar_sdk.sh --comprobar
   bash 04-Proyecto-Base/deploy/gcp/instalar_sdk.sh
   ```
   Qué debes ver (según el script): líneas `[OK   ]` y `SDK LISTO`.
2. **Inicia sesión** sin pegar claves: `gcloud auth login --no-launch-browser`, y comprueba con `gcloud auth list`. Para que Python lea BigQuery (paso 7) hacen falta además credenciales por defecto de aplicación: el propio programa indica `gcloud auth application-default login` si faltan (en el Codespace, con `--no-launch-browser`; sin verificar).
3. **Tus variables**, en `04-Proyecto-Base`:
   ```bash
   cp deploy/gcp/env.ejemplo.sh deploy/gcp/env.sh
   ```
   Abre `deploy/gcp/env.sh` en el editor y rellena `CURSO_GCP_PROYECTO`, `CURSO_GCP_REGION` (una sola región para todo; elígela tú tras mirar qué servicios están disponibles en ella), `CURSO_GCP_CUENTA_FACTURACION` y `CURSO_GCP_PRESUPUESTO_IMPORTE`. **`env.sh` está en `.gitignore`: no lo subas nunca.** Los scripts lo cargan solos.
4. **Para tu caso**, añade en `env.sh` (son variables que leen los scripts):
   ```bash
   export CURSO_GCP_DB="/ruta/absoluta/a/TU_BASE.db"     # datos.sh: tu SQLite (absoluta, o relativa a 04-Proyecto-Base)
   export CURSO_GCP_TABLAS="master_llamadas master_descartes master_calidad fs_llamada fs_catalogo ml_dataset ml_particiones"   # TUS tablas, separadas por espacios
   ```
   **Importante:** si no fijas `CURSO_GCP_TABLAS`, `datos.sh` carga las **10 tablas del caso Retail**, que no existen en tu base.

**Qué debes ver:** vuelve a lanzar `bash deploy/gcp/datos.sh` (modo «mostrar»): ya no salen `TU-PROYECTO` ni `TU-REGION`, sino tus valores, y la carga lista **tus** tablas.
**Si falla:** `gcloud` no se reconoce → repite el instalador; `PERMISSION_DENIED` → cuenta equivocada (`gcloud auth list`).

## 6. Comprobación previa, APIs y presupuesto (ruta A · 15 min · NUBE · sin verificar)

```bash
bash deploy/gcp/preparar_proyecto.sh --comprobar
bash deploy/gcp/preparar_proyecto.sh --ejecutar
```

`--comprobar` solo **lee** (versión de `gcloud`, que hay una cuenta activa sin imprimir el correo, el proyecto, la facturación y las APIs habilitadas). `--ejecutar` habilita **solo** las APIs que lista el script (Storage, BigQuery, Artifact Registry, Cloud Run, Secret Manager, IAM, Facturación y Presupuestos) y crea el presupuesto `curso-ml-presupuesto` con avisos al 50 %, 90 % y 100 % del importe que elegiste.

**Qué debes ver** (según el código, sin verificar): `### MODO COMPROBAR: solo lecturas (no crea ni borra nada).`, `OK: hay una cuenta activa.`, `OK: facturacion habilitada.`; con `--ejecutar`, `### MODO REAL: ...` y el presupuesto al final en `gcloud billing budgets list`.
**Si falla:** `La facturacion NO esta habilitada` → vincúlala o pasa a la ruta B. Si tu cuenta no deja crear el presupuesto por la línea de órdenes, créalo en la consola (lo dice el propio script). Habilitar APIs puede tardar: repite la orden.
**Coste:** habilitar APIs no crea recursos; el presupuesto no cuesta (según el script; consulta la consola).

## 7. Datos: bucket, BigQuery y validación (ruta A · 30 min · NUBE · sin verificar)

```bash
bash deploy/gcp/datos.sh            # repasa lo que hará
bash deploy/gcp/datos.sh --ejecutar
```

Qué hace, en orden (ver [`mostrar-datos.txt`](ensayo-local/mostrar-datos.txt)): inventario; **bucket** privado en tu región con acceso uniforme, prevención de acceso público y etiqueta `curso=ml-ia`; **exporta** a Parquet en `/tmp/curso-gcp-parquet`, lo **sube** a `gs://…/parquet`, lo **descarga** de vuelta y **verifica el SHA-256** (Cloud Storage informa de MD5 y CRC32C, no de SHA-256: por eso se descarga y se recalcula); **dataset** en la misma ubicación, con caducidad de tablas de 7 días (decisión nuestra) y etiqueta; **una carga** `bq load --source_format=PARQUET` por tabla; y **validación** contra BigQuery, con dry run y tope de bytes en cada consulta (por defecto 1 000 000 000 bytes, decisión nuestra; `CURSO_GCP_MAX_BYTES`), que guarda `/tmp/curso-gcp-parquet/validacion-bigquery.json`.

**Qué debes ver** (deducido del código y del ensayo local, sin verificar): la verificación de huella con todas las líneas `coincide ... huella igual`; la validación con `RESULTADO: coincide` y una línea `BigQuery: N consultas, M bytes estimados por dry run (tope por consulta: ...)`. Contra BigQuery **no** hay comprobaciones de huella (esas se hacen en el bucket), así que salen menos comprobaciones que en local (con la base del curso serían 50 en vez de 62).
**Si falla:**
- `Falta la biblioteca google-cloud-bigquery` → el entorno del curso la incluye en su lista de paquetes; comprueba que el Python es el de `env-ia-mlops` (`CURSO_GCP_PYTHON`).
- `DIFIERE` en `esquema` → el tipo llegó distinto a BigQuery: anótalo (la equivalencia de tipos está sin verificar) y **no sigas** hasta entenderlo.
- `La consulta procesaria unos N bytes y el tope es ...: no se ejecuta` → es el freno de coste funcionando; sube el tope solo si sabes por qué.
- El nombre del bucket ya existe → los nombres de bucket son globales: cambia `CURSO_GCP_PREFIJO` (o `CURSO_GCP_BUCKET`).

**Coste:** almacenamiento en el bucket y en BigQuery y las consultas de validación; consulta la consola.
**Pendiente en los scripts:** la subida de los **archivos originales** (`data/raw`, o tu CSV de Bank Marketing con su `SHA256SUMS`) no está en `datos.sh`: hoy solo se suben los Parquet con su manifiesto. Si quieres subir los originales, genera antes su manifiesto **en una copia** de la carpeta (`python -m ia_mlops.migracion huella generar COPIA`, que escribe `MANIFEST.sha256` dentro de ella) y anota en la evidencia que es un paso fuera de los scripts.

## 8. Secreto y cuenta de servicio mínima (ruta A · 15 min · NUBE · sin verificar)

```bash
bash deploy/gcp/secretos_y_cuenta.sh --ejecutar
```

Crea un **secreto** (`curso-ml-demo-secreto`) con **un valor aleatorio sin significado** que nunca se imprime, una **cuenta de servicio** (`sa-retencion-api`) **sin claves**, y le concede **un solo rol**, `roles/secretmanager.secretAccessor`, **sobre ese secreto**. Ningún rol de Storage ni de BigQuery: la API no los usa.

**Qué debes ver** (según el script, sin verificar): la política del secreto con la cuenta de servicio; una versión del secreto; la lista de **claves de usuario vacía**; y la política del proyecto filtrada por la cuenta **vacía**. Pega esas tres comprobaciones en la evidencia.
**Si falla:** `PERMISSION_DENIED` → tu usuario no es propietario del proyecto. API no habilitada → paso 6.
**Coste:** versiones y accesos de secretos; consulta la consola.

## 9. Medir la memoria y publicar la imagen (ruta A · 30 min · NUBE · sin verificar)

**Primero mide**, en el Codespace (no adivines la memoria):

```bash
make pipeline
make imagen
make contenedor          # en una terminal; déjala abierta
docker stats --no-stream # en otra terminal, mientras haces un par de peticiones a http://127.0.0.1:8080
```

Anota la memoria que ves y fija `CURSO_GCP_MEMORIA` en `env.sh` con un margen que tú decidas (formato del `--memory` de `gcloud run deploy`; sin verificar). Si la dejas vacía, no se fija.

**Después publica:**

```bash
bash deploy/gcp/imagen.sh --ejecutar
```

Crea el repositorio `curso-ml-imagenes` (Docker, tu región, etiqueta), configura Docker con el **ayudante de credenciales de gcloud** (sin claves en disco), construye, etiqueta y empuja con la etiqueta fija `s3-1` (nunca `latest`; `CURSO_GCP_ETIQUETA_IMAGEN`).

**Qué debes ver** (sin verificar): el `docker push` y, al final, el listado de imágenes con su etiqueta y su resumen (*digest*). Apunta el resumen.
**Si falla:** `make pipeline` no hecho → la imagen no lleva modelo. `denied` al empujar → repite `gcloud auth configure-docker` con tu región (lo hace el script). El empuje es lento (una imagen de cientos de MB): espera.
**Tu caso:** `imagen.sh` construye `deploy/docker/Dockerfile` **del proyecto base del curso**. Para publicar tu propia imagen del avance 2, usa como plantilla las órdenes `docker tag` y `docker push` que el script imprime en modo «mostrar», con el nombre de tu imagen (`CURSO_GCP_IMAGEN`) y tu propio `docker build` (sin verificar). Si no tienes imagen propia, publica la del curso y **decláralo**.
**Coste:** almacenamiento de la imagen en Artifact Registry (se acumula con cada versión); consulta la consola.

## 10. Cloud Run privado (ruta A · 15 min · NUBE · sin verificar)

```bash
bash deploy/cloud-run/desplegar.sh --ejecutar
```

Despliega `retencion-api` **privado** (`--no-allow-unauthenticated`), con mínimo de instancias 0, máximo 2 (`CURSO_GCP_MAX_INSTANCIAS`), puerto 8080, la cuenta de servicio del paso 8, el secreto como variable `CURSO_DEMO_SECRETO` en su **versión 1** y `CURSO_LOG_NIVEL=INFO`. Recuerda: **la API no lee ese secreto ni BigQuery** (teoría, apartado 1).

**Qué debes ver** (sin verificar): la URL del servicio y la cuenta de servicio en `services describe`; en la política del servicio, **ningún `allUsers`**. Pega ambas en la evidencia.
**Si falla:** la revisión no arranca → tu contenedor debe escuchar en el **8080** (como el de S2); mira los registros (paso 11). Permiso denegado sobre el secreto → revisa el paso 8.
**Coste:** instancias mientras atienden peticiones; con mínimo 0 no hay instancia en reposo (según el script); consulta la consola.

## 11. Probar el servicio y leer sus registros (ruta A · 25 min · NUBE · sin verificar)

```bash
bash deploy/cloud-run/probar.sh --ejecutar
```

Abre un **proxy local** en el puerto 8081 con tu identidad (sin hacer público el servicio ni tocar el código), llama a `/salud`, `/listo`, `/modelo` y `/predecir` con `tests/datos/cliente_ejemplo.json` y una cabecera `X-Request-ID: prueba-s3-<número>`, ejecuta `python -m ia_mlops.modeling.comparar --url http://127.0.0.1:8081` y lee los registros del servicio. Cierra el proxy al terminar.

**Qué debes ver** (esperado según S2, sin verificar en Cloud Run): `{"estado":"ok"}`, `{"estado":"listo"}`, la ficha del modelo y la probabilidad del cliente de ejemplo, que en local con la muestra es `0.8278889191932133` (los últimos decimales pueden variar); `comparar` con diferencias cero; en los registros, la línea JSON con tu `prueba-s3-<número>` y **ningún dato del cliente**.
**Provoca un 422** y búscalo en los registros: abre el proxy a mano con la orden que imprime el script (`gcloud run services proxy retencion-api --project ... --region ... --port 8081`) y, en otra terminal, repite la petición de S2 con `tests/datos/casos/02_recencia_negativa.json` contra `http://127.0.0.1:8081/predecir`.
**Si falla:** el proxy tarda más de los 5 s que espera el script → repite. `comparar` necesita el modelo local (`make pipeline`). Si el puerto 8081 está ocupado, cambia `CURSO_GCP_PUERTO_PROXY`.
**Tu caso:** las rutas, el ejemplo y `comparar` son del proyecto del curso. Con tu servicio, abre el proxy con la orden anterior y haz tus peticiones con tu propio JSON de ejemplo (sin verificar).
**Coste:** peticiones al servicio y lectura de registros; consulta la consola.

## 12. (Opcional) Segunda revisión y vuelta atrás (ruta A · 15 min · NUBE · sin verificar)

Volver a desplegar crea una **revisión** nueva del servicio; volver atrás es devolver el tráfico a la anterior. **Los scripts del curso no traen la orden de reparto de tráfico** (pendiente): si lo haces, búscala en la ayuda de `gcloud run` y en la documentación de Cloud Run, y anota en la evidencia la orden exacta que usaste y su salida.

## 13. Plan de rollback hacia lo local (rutas A y B · 15 min · texto)

Escribe, en media página: (1) **qué señal** te hace volver (validación que difiere, servicio que no queda listo, gasto inesperado); (2) **qué apagas** en la nube (paso 14); (3) **qué arrancas** en local (tu SQLite y tu imagen siguen ahí: `make api` o `make contenedor`); (4) **cómo compruebas** que lo local funciona (`/listo` y una predicción). Nada de lo local se borra al migrar.

## 14. Limpieza y listados vacíos (ruta A · 20 min · NUBE · sin verificar)

**`limpiar.sh` todavía no existe (pendiente).** Mientras tanto, borra a mano, **en este orden**: servicio de Cloud Run → repositorio de imágenes → secreto → cuenta de servicio → dataset → bucket. Las órdenes de abajo **no están en los scripts ni se han ejecutado**: son la forma habitual de la documentación de `gcloud`/`bq`; compruébalas con `--help` antes. Usan los nombres por defecto: si cambiaste el prefijo o los nombres, usa los que te imprimió el modo «mostrar». Ninguna lleva `--quiet`: cada una te pedirá confirmación.

```bash
source deploy/gcp/env.sh
P="$CURSO_GCP_PROYECTO"; R="$CURSO_GCP_REGION"

gcloud run services delete retencion-api --project "$P" --region "$R"
gcloud artifacts repositories delete curso-ml-imagenes --project "$P" --location "$R"
gcloud secrets delete curso-ml-demo-secreto --project "$P"
gcloud iam service-accounts delete "sa-retencion-api@$P.iam.gserviceaccount.com" --project "$P"
bq --project_id "$P" rm -r -d "$P:curso_ml"
gcloud storage rm --recursive "gs://$P-curso-ml-datos"
```

**Listados de comprobación** (pégalos en la evidencia; sin verificar):

```bash
gcloud run services list --project "$P" --region "$R"
gcloud artifacts repositories list --project "$P" --location "$R"
gcloud secrets list --project "$P"
gcloud iam service-accounts list --project "$P"
bq --project_id "$P" ls
gcloud storage ls --project "$P"
```

**Qué debes ver:** todos vacíos; en las cuentas de servicio **no debe aparecer `sa-retencion-api`** (pueden aparecer cuentas que crea Google; sin verificar). El presupuesto puedes dejarlo (`gcloud billing budgets list --billing-account "$CURSO_GCP_CUENTA_FACTURACION"`, la orden de `preparar_proyecto.sh`).

**Si dudas de haber borrado todo, borra el proyecto entero** (sin verificar; consulta en la documentación el plazo durante el que se puede recuperar):

```bash
gcloud projects delete "$P"
```

**En local:** `rm -rf /tmp/curso-gcp-parquet /tmp/curso-gcp-parquet-descarga /tmp/s3-parquet`; cierra la sesión con `gcloud auth revoke` (y, si usaste credenciales de aplicación, revócalas también; sin verificar); **para y borra el Codespace** si ya no lo necesitas. **Al día siguiente**, mira Facturación y anota **lo que veas**, sin cifras inventadas.
**Coste:** borrar no cuesta; lo que no borres sigue pudiendo cobrar.

## 15. Evidencia de la práctica (rutas A y B · 20 min · texto)

Qué y cuándo se entrega lo fija la tarea de S4; mientras tanto, esta es la lista de lo que conviene guardar. Pega **texto**, no solo capturas, y **tapa correos, IDs de proyecto y de facturación y cualquier token**:

1. Inventario (paso 3) y estrategia por pieza.
2. Carpeta del ensayo local (paso 4): `inventario.txt`, `exportar.txt` (con el `MANIFEST.sha256`), `validar.txt`, `validar-rotura.txt`.
3. Ruta A: verificación de huella tras descargar, `validacion-bigquery.json` y su `RESULTADO`.
4. Identidad: las tres comprobaciones del paso 8 (y por qué ese único rol).
5. Imagen: nombre, etiqueta y resumen. Servicio: región, privado, mínimo y máximo de instancias, memoria medida.
6. Pruebas del servicio y la línea de registro de tu `X-Request-ID` (sin datos del cliente) y la del 422.
7. Costes: **lo que viste en la consola**, con la fecha. Sin estimaciones.
8. Plan de rollback (paso 13). Limpieza: **los listados vacíos** del paso 14.
9. **Qué no pudiste ejecutar** y por qué (por ejemplo, «ruta B: sin facturación»). Ayuda recibida.

---

## B. Ruta sin nube: el plan escrito (30 min)

Si sigues la ruta B, además de los pasos 1–4, 13 y 15, entrega un **plan de migración escrito** que demuestre que sabrías hacerlo:

1. **Salida de los scripts en modo «mostrar» con tus valores ficticios** o con los marcadores `TU-...` (paso 2), y con `CURSO_GCP_DB` y `CURSO_GCP_TABLAS` apuntando a tu caso (así `bash deploy/gcp/datos.sh` lista la carga de **tus** tablas). Para fijarlas sin `env.sh`: `CURSO_GCP_DB=... CURSO_GCP_TABLAS="..." bash deploy/gcp/datos.sh`.
2. Para cada recurso que crearías: **qué es** (bucket, dataset, repositorio, secreto, cuenta de servicio, servicio), **qué estrategia** aplica, **qué puede costar** (sin cifras) y **con qué orden se borra** (paso 14).
3. La **identidad mínima**: qué rol tendría la cuenta de servicio, sobre qué recurso, y por qué no otro.
4. El **orden**: presupuesto antes que nada, validación antes que despliegue, limpieza el mismo día.
5. Una frase clara: **«No ejecutado en GCP: ruta sin nube»**.

## Cómo se rompe (autoestudio, sin verificar)

Tres fallos típicos para provocar **solo si ya tienes la ruta A funcionando**, anotando el mensaje exacto: (1) **permiso denegado**: quita el rol del paso 8 y mira qué registra la revisión al arrancar; (2) **503**: el servicio arranca pero no está listo (el caso de S2 sin modelo); (3) **bucket en otra región** que el dataset: la carga debería fallar (según la documentación; sin verificar). Repara cada uno antes de limpiar.

## Si falla (resumen)

| Síntoma | Qué probar |
|---|---|
| `Opcion desconocida` o `--confirmar es solo de limpiar.sh` | Solo existen `--ejecutar`, `--comprobar` y `--ayuda` (`--confirmar` es de `limpiar.sh`, que aún no existe) |
| `Faltan variables de entorno: CURSO_GCP_PROYECTO CURSO_GCP_REGION` | Falta `deploy/gcp/env.sh` o está vacío (paso 5) |
| `La etiqueta de la imagen no puede ser latest` | Usa una etiqueta fija (`CURSO_GCP_ETIQUETA_IMAGEN`) |
| `Falta 'gcloud' en el PATH` | Instala el SDK (paso 5); en modo «mostrar» no hace falta |
| `PERMISSION_DENIED` | Cuenta o proyecto equivocados (`gcloud auth list`, `env.sh`) |
| `RESULTADO: DIFIERE` | Para: la migración no está bien. Mira qué comprobación falla y en qué tabla |
| El servicio no queda listo | Registros del paso 11; puerto 8080; modelo dentro de la imagen (`make pipeline`) |
| No tengo facturación | Ruta B |
