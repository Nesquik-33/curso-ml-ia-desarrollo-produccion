# S3 · Teoría y glosario: de local a GCP

> **Material de preparación para S4: en la S3 del 20/11 GCP solo se explica; la práctica es en S4** (miércoles 25/11). La tarea de S3 no es esta migración: consulta la tarea de la sesión.

Material de lectura sobre «De local a GCP: migración y despliegue»: en la S3 se cuenta de palabra y en la S4 se practica. Acompaña a la presentación y a la [guía de laboratorio](../practica/guia-laboratorio.md).

> **Estado (20/11/2026).** Hasta hoy **no se ha ejecutado nada en Google Cloud**. Lo único ejecutado es el **ensayo local** de la migración (SQLite → Parquet → validación, con una rotura deliberada) y los scripts de despliegue en **modo «mostrar»** (imprimen las órdenes sin ejecutarlas); sus salidas están en [`practica/ensayo-local/`](../practica/ensayo-local/). Todo lo que dependa de la nube (órdenes, opciones, nombres de roles, tipos resultantes en BigQuery, tiempos, comportamiento del presupuesto, costes) va marcado **sin verificar**. No hay ni una cifra de precios, cuotas o créditos gratuitos en este documento, y no la habrá hasta que se mire en la consola.

## 1. De dónde partimos

En S1 y S2 todo corría «en local» (tu equipo o el Codespace): los archivos originales en `data/raw`, la base SQLite con las capas `raw_`, `master_`, `fs_` y `ml_`, el modelo registrado con MLflow, la API de FastAPI servida con `uvicorn` y su imagen Docker. Eso hace de **on-premise simulado**: la situación de partida de muchos equipos. Este material explica cómo llevarlo a GCP sabiendo **qué se mueve, cómo se comprueba que llegó bien y cuánto cuidado de costes hace falta**.

### El mensaje honesto de esta sesión

La API de S2 **no lee datos ni usa secretos**: el modelo va **dentro de la imagen** y su única variable de configuración es `CURSO_LOG_NIVEL`. Quien lee datos es la **interfaz** (`ia_mlops/interfaz/`), que abre la SQLite en solo lectura.

Por tanto:
- Desplegar la API en Cloud Run **no la hace «apuntar» a BigQuery**. BigQuery recibe una **copia analítica validada** de las tablas; el servicio sigue sirviendo el modelo que lleva dentro.
- El secreto de la demo es un **valor de ejemplo, aleatorio y sin significado**: sirve para aprender el mecanismo (Secret Manager, versión, permiso, montaje en Cloud Run). **El servicio actual no lo consume.**
- Que la interfaz consulte BigQuery sería un **refactor** que queda fuera de S3. Datos y servicio se migran **por separado**, y eso es una decisión de diseño, no un olvido.

## 2. Las fases de una migración

| Fase | Pregunta que responde | En el caso del curso |
|---|---|---|
| **Evaluar** | ¿Qué hay y de qué depende? | Inventario: archivos, tablas con filas y columnas, variables y secretos, servicio, imagen, MLflow. `python -m ia_mlops.migracion inventario` cubre las **tablas**; el resto se completa a mano |
| **Planificar** | ¿En qué orden, con qué riesgos y cómo vuelvo atrás? | Proyecto desechable, presupuesto **antes** que cualquier recurso, una sola región, estrategia por pieza, plan de limpieza y plan de rollback **escritos antes de crear nada** |
| **Ejecutar** | ¿Lo movimos y llegó bien? | Subir, cargar, **validar** (conteos, esquemas, agregados, muestra; código de salida distinto de 0 si algo difiere), publicar la imagen, desplegar, probar y leer registros |
| **Optimizar** | ¿Cuesta lo que debe y se puede operar? | Tamaños mínimos, mínimo de instancias 0, caducidad de tablas, mirar la facturación y **borrar lo que ya no sirve** |

Los nombres de las fases **no se han contrastado** hoy con la documentación vigente de Google Cloud (sin verificar: puede usar otros nombres u otra división). La idea que importa es que **validar** y **limpiar** forman parte de la migración, no son un extra.

## 3. Estrategias: las tres «R» que se practican

| Estrategia | Qué es | Ejemplo en S3 |
|---|---|---|
| **Rehost** (*lift and shift*) | Mover tal cual, sin cambiar la pieza | La imagen Docker de S2 pasa a Artifact Registry y se ejecuta en Cloud Run **sin tocar el código** |
| **Replatform** | Mover cambiando la plataforma, con ajustes mínimos | SQLite → BigQuery (vía Parquet); archivos → Cloud Storage; `.env` → Secret Manager; ficheros de log → Cloud Logging |
| **Refactor** | Rediseñar para aprovechar la nube | Identidad: de «mi usuario y una clave» a una **cuenta de servicio con un solo permiso y sin claves**; más adelante, scripts manuales → workflow orquestado e identidad federada |

Las otras tres «R» que suelen citarse (**retener**: dejarlo donde está; **retirar**: apagarlo porque ya no aporta; **recomprar**: sustituirlo por un producto comprado) solo se mencionan; no hay práctica. Hay listas de «R» con más o menos elementos según la fuente (sin verificar cuál usa hoy Google Cloud).

## 4. Mapa de equivalencias, con la estrategia de cada pieza

| Pieza del curso | Hoy (local) | En GCP | Estrategia | En S3 |
|---|---|---|---|---|
| Archivos (`data/raw`, Parquet exportados) | carpeta | **Cloud Storage** (un bucket) | Replatform | Practicado: `deploy/gcp/datos.sh` (sube los Parquet con su `MANIFEST.sha256`) |
| Capas `master_`, `fs_`, `ml_` | SQLite | **BigQuery** (un dataset, una tabla por capa) | Replatform | Practicado: `datos.sh` + `python -m ia_mlops.migracion validar --bigquery` |
| Configuración sensible | `.env` | **Secret Manager** (secreto con versiones) | Replatform | Practicado con un valor de ejemplo: `deploy/gcp/secretos_y_cuenta.sh` |
| Identidad del servicio | tu usuario | **Cuenta de servicio** sin claves, un permiso | Refactor | Practicado: `secretos_y_cuenta.sh` |
| Imagen | Docker local | **Artifact Registry** (repositorio Docker) | Rehost | Practicado: `deploy/gcp/imagen.sh` |
| Servicio | `uvicorn` / `docker run` | **Cloud Run** (privado) | Rehost | Practicado: `deploy/cloud-run/desplegar.sh` y `probar.sh` |
| Registros | líneas JSON por la salida estándar | **Cloud Logging** | Replatform | Practicado: lectura de registros en `probar.sh` (el registro JSON de S2 ya sirve, sin cambiar código) |
| Costes | hardware fijo | **Presupuesto y alertas** de facturación | Nuevo | Practicado: `deploy/gcp/preparar_proyecto.sh` |
| Seguimiento y registro de modelos | MLflow con SQLite y carpeta | MLflow con Cloud SQL y Cloud Storage, o Vertex AI Experiments y Model Registry | Replatform | **Solo se menciona** |
| Tareas programadas | `cron` | Cloud Scheduler | Replatform | **Solo se menciona** |
| Orquestación del pipeline | scripts a mano | Vertex AI Pipelines, Cloud Composer, Cloud Build | Refactor | **Solo se menciona** (en el curso orquesta GitHub Actions) |

GKE (Kubernetes gestionado) aparece en el extra como alternativa a Cloud Run; la demo de GKE es solo del instructor y está **sin ejecutar**.

## 5. Inventario: lo primero, antes de mover nada

Un inventario responde: **qué hay, cuánto ocupa, de qué depende y qué se migra (y qué no, y por qué)**. Para el caso del curso:

| Qué | Cómo se obtiene | Ejemplo real (ensayo local) |
|---|---|---|
| Tablas que se migran, con filas, columnas y clave | `python -m ia_mlops.migracion inventario --db data/processed/curso.db` | 10 tablas `master_`/`fs_`/`ml_`, 29 743 filas en total ([`inventario.txt`](../practica/ensayo-local/inventario.txt)) |
| Tablas que **no** se migran y por qué | la misma orden | 7 tablas (`raw_*` y `control_pipelines`): «no empieza por un prefijo elegido» |
| Archivos originales y su huella | a mano + `python -m ia_mlops.migracion huella generar CARPETA` | en el caso del alumnado ya existe `02-Proyecto-Transversal/datos/SHA256SUMS` |
| Variables de entorno y secretos | **a mano** (la orden `inventario` no los detecta) | API: solo `CURSO_LOG_NIVEL`; ningún secreto real |
| Servicio, imagen, puertos | **a mano** | `retencion-api`, puerto 8080, usuario 10001, `/salud` y `/listo` |
| Modelo y MLflow | **a mano** | el modelo va dentro de la imagen; MLflow no se migra en S3 |

El inventario decide la **estrategia por pieza** (tabla del apartado 4) y lo que queda fuera.

## 6. Integridad y validación: «llegó bien» se demuestra con código

**Huella SHA-256.** `python -m ia_mlops.migracion exportar` escribe en la carpeta de salida un Parquet por tabla, `esquema.json`, `conteos.json` y un **`MANIFEST.sha256`** con la huella de cada uno de esos archivos (formato de `sha256sum`: «huella, dos espacios, nombre»). Para otra carpeta cualquiera (por ejemplo, una copia de los archivos originales), `python -m ia_mlops.migracion huella generar CARPETA` escribe el `MANIFEST.sha256` **dentro de esa carpeta**, y `huella verificar CARPETA` lo comprueba.

**Lo que Cloud Storage no hace.** Cloud Storage informa de **MD5 y CRC32C** de cada objeto, **no de SHA-256** (comprobar en la documentación vigente: sin verificar hoy). Por eso el SHA-256 es la huella del **origen local**, y la integridad de lo subido se comprueba **descargándolo y recalculando su SHA-256** (es lo que hace `datos.sh`: `gcloud storage rsync` de vuelta a una carpeta y `huella verificar`), o guardando la huella como metadato propio del objeto. No se lee un SHA-256 «del bucket», porque no existe.

**Validación de tablas.** `python -m ia_mlops.migracion validar` compara origen (SQLite) y destino (carpeta de Parquet o BigQuery) tabla a tabla: **existe**, **esquema** (nombres, orden y tipos lógicos: entero, real, texto, binario), **filas**, **agregados** (nulos, distintos, mínimo, máximo y suma por columna) y una **muestra** de las primeras y últimas filas por clave. Sale con **0** si todo coincide, **1** si el destino difiere y **2** si el uso es incorrecto. En el ensayo local: 62 comprobaciones, todas «coincide»; y tras borrar **una** fila de `master_lineas`, «DIFIERE» en filas, agregados, muestra y huella ([`validar-rotura.txt`](../practica/ensayo-local/validar-rotura.txt)). Una captura de la consola no demuestra esto; el código y su salida, sí.

**Contra BigQuery** (sin verificar): cada consulta se lanza antes en **dry run** y se rechaza si supera un tope de bytes que fijamos nosotros (`--max-bytes`); la consulta real lleva ese mismo tope. La equivalencia de tipos SQLite → BigQuery (INT64, FLOAT64, STRING, BYTES) está **sin verificar** con una cuenta real. La validación contra BigQuery no incluye las comprobaciones de huella (eso se hace en el bucket).

## 7. IAM y mínimo privilegio

- **IAM** decide **quién** (una persona o una cuenta de servicio) puede hacer **qué** (un rol, que agrupa permisos) **sobre qué** (el proyecto entero o un recurso concreto).
- **Mínimo privilegio:** lo que no se necesita no se concede. La API no lee ni Storage ni BigQuery, así que su cuenta de servicio **no recibe roles de Storage ni de BigQuery**.
- En la demo, la cuenta `sa-retencion-api` recibe **un solo rol**, `roles/secretmanager.secretAccessor`, concedido **sobre ese secreto** y no sobre el proyecto (es el rol que figura en `secretos_y_cuenta.sh`; su nombre exacto está sin verificar contra GCP). La comprobación es que la cuenta **no aparece** en la política del proyecto (listado vacío).
- **Excepción declarada:** en su proyecto desechable, el instructor (y tú en el tuyo) actúa como **propietario**. Es aceptable en un proyecto personal de prácticas y se dice en voz alta; no es lo que se hace en un equipo.
- Mejora mencionada, sin práctica: hacer las cargas con una cuenta de servicio y suplantación en vez de con tu usuario.

## 8. Secretos sin claves JSON

- Un **`.env` en el repositorio** o una **clave JSON de cuenta de servicio** son credenciales copiables: quien tenga el archivo actúa como esa identidad, desde cualquier sitio, hasta que alguien la revoque. Se filtran en commits, capturas y chats.
- **Secret Manager** guarda el valor fuera del código, con **versiones** y con permiso por secreto; Cloud Run lo inyecta como variable de entorno **en una versión fija** (en el script, la versión 1, no «latest»). El valor **nunca se imprime**.
- **Sin claves JSON:** la cuenta de servicio no tiene claves de usuario (el script comprueba que su lista sale vacía). Docker se autentica con el **ayudante de credenciales de gcloud** (`gcloud auth configure-docker`), sin clave en disco. Tú te autenticas con `gcloud auth login`, sin pegar nada fuera del terminal que lo pide.
- La autenticación de GitHub Actions con GCP **sin claves** (Workload Identity Federation) no entra en este material.

## 9. Regiones

- **Una sola región para todo** (bucket, dataset, repositorio de imágenes, secreto y servicio). Lo fija cada persona en `CURSO_GCP_REGION`; los scripts no traen ninguna.
- El dataset de BigQuery debe estar en la **misma ubicación** que el bucket desde el que se carga (comprobar en la documentación vigente: sin verificar).
- **Criterios para elegir:** que todos los servicios usados estén disponibles en ella, cercanía y la política de tu organización. **Aquí no se afirma qué región es mejor ni más barata**: la decisión del curso está abierta y las guías usan nombres de región solo como ejemplos de la documentación de Google.
- Mover datos entre regiones puede tener coste de red (sin cuantificar).

## 10. Costes: qué puede cobrar y cómo no llevarse sorpresas

**Sin cifras.** Los precios cambian y no se han medido: consulta la página de precios de cada servicio y la consola de facturación de tu proyecto.

Lo que **puede** generar coste en S3 (sin cuantificar, sin verificar): almacenamiento en el bucket y en Artifact Registry (una imagen de cientos de MB se acumula con cada versión), almacenamiento y consultas de BigQuery, instancias de Cloud Run mientras atienden peticiones, versiones y accesos de secretos, y salida de red entre regiones.

Cómo se controla:
1. **Proyecto nuevo y desechable** (borrarlo entero es la limpieza de último recurso).
2. **Presupuesto con alertas antes que cualquier recurso.** Una alerta de presupuesto **avisa, no corta el gasto** (es lo que asume el curso: compruébalo en la documentación vigente).
3. **Valores seguros por defecto:** nada público, mínimo de instancias 0 y máximo bajo, caducidad por defecto de las tablas (7 días: una decisión nuestra, no una cifra de Google), consultas con dry run y tope de bytes, etiqueta `curso=ml-ia` en todo lo que la admite.
4. Scripts en **modo «mostrar» por defecto**: no crean nada sin `--ejecutar`.
5. **Borrar todo el mismo día** y comprobarlo con listados vacíos; al día siguiente, mirar la facturación y anotar **lo que se vea**, sin extrapolar.

## 11. Rollback: cómo vuelvo atrás

- **Del servicio:** cada despliegue en Cloud Run crea una **revisión** nueva; volver atrás es devolver el tráfico a una revisión anterior (concepto; la orden no está en los scripts del curso: sin verificar).
- **Hacia lo local:** nada de lo local se borra al migrar. La imagen sigue en tu Docker, la SQLite y los archivos siguen en tu carpeta, y la API sigue arrancando con `make api` o `make contenedor`. El plan de rollback es un texto corto que dice: qué señal hace volver (validación que no coincide, servicio que no queda listo, coste inesperado), qué se apaga en la nube, qué se arranca en local y cómo se comprueba que funciona.
- Por eso el orden de la guía es: **validar antes de seguir**, y **no borrar lo local** hasta que lo de la nube esté comprobado (y en el curso, ni entonces).

## 12. Qué se afirma y qué no

| Se afirma (ejecutado, con salida guardada) | No se afirma (sin verificar) |
|---|---|
| La exportación SQLite → Parquet de las 10 tablas (29 743 filas, 444 856 bytes de Parquet) y su `MANIFEST.sha256`, en local | Que BigQuery cargue esos Parquet con esos tipos |
| La validación local: 62 comprobaciones «coincide»; una fila borrada se detecta | Cuánto tarda subir, cargar, empujar la imagen o desplegar |
| Las pruebas de la migración pasan en local (`tests/test_migracion.py`) | Los nombres exactos de opciones y roles de `gcloud`/`bq` |
| Los scripts de `deploy/` en modo «mostrar» imprimen sus órdenes sin ejecutar nada | Que `gcloud run services proxy` y `comparar` funcionen sobre Cloud Run |
| La API de S2 no lee datos ni secretos | Cualquier precio, cuota, crédito gratuito o región «mejor» |
| | Qué hace exactamente una alerta de presupuesto y con qué retraso aparecen los cargos |

## 13. Glosario

| Término | Qué es |
|---|---|
| **Bucket** | Contenedor de objetos (archivos) de Cloud Storage, con una ubicación. En la demo, uno solo, privado, con acceso uniforme y prevención de acceso público |
| **Objeto** | Un archivo dentro de un bucket. Cloud Storage guarda de él MD5 y CRC32C (no SHA-256; sin verificar) |
| **Dataset** (conjunto de datos) | Agrupación de tablas de BigQuery con una ubicación. Su nombre admite guion bajo, no guion (`curso_ml`) |
| **Tabla** | Datos con esquema dentro de un dataset; en la demo, una por cada tabla `master_`/`fs_`/`ml_`, con caducidad por defecto |
| **Job de carga** | Tarea de BigQuery que lee archivos (aquí Parquet desde el bucket) y los escribe en una tabla (`bq load`) |
| **Parquet** | Formato de archivo por columnas que conserva los tipos; es el puente entre SQLite y BigQuery. Necesita `pyarrow` |
| **Huella (SHA-256)** | Resumen que cambia si cambia un solo byte; `MANIFEST.sha256` guarda la de cada archivo |
| **Repositorio** (Artifact Registry) | Almacén de imágenes de contenedor en una región; se direcciona como `REGION-docker.pkg.dev/PROYECTO/REPOSITORIO` |
| **Imagen** | Paquete inmutable con el código, las dependencias y el modelo; se identifica por etiqueta (`s3-1`; nunca `latest`) o por resumen (*digest*) |
| **Revisión** | Versión inmutable de un servicio de Cloud Run: cada despliegue crea una; el tráfico se reparte entre revisiones |
| **Cuenta de servicio** | Identidad de una aplicación, no de una persona; en la demo, sin claves y con un solo permiso |
| **Rol** | Conjunto de permisos que se concede a una identidad sobre un recurso (por ejemplo, el de acceso al valor de un secreto) |
| **Secreto y versión** | El secreto es el nombre y su política de acceso; cada valor que se guarda es una versión. Se usa una versión fija |
| **Registro** | Línea que deja el servicio (aquí, JSON con `id` de petición y código, sin datos del cliente); Cloud Logging las recoge |
| **Presupuesto** | Importe que eliges para tu cuenta de facturación, con alertas por umbrales; **avisa, no corta** (a comprobar) |
| **Etiqueta** (`curso=ml-ia`) | Par clave-valor que se pone a los recursos para localizarlos y borrarlos |
| **Región** | Lugar físico donde vive un recurso; en el curso, una sola para todo |
| **Modo «mostrar»** | Comportamiento por defecto de los scripts del curso: imprimen las órdenes sin ejecutarlas; crear exige `--ejecutar` |
