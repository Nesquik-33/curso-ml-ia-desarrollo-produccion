# Planificación de S3 · De local a GCP: migración y despliegue

Estado: **propuesta del 15/11/2026, para revisión del instructor.** Solo planifica: no hay todavía código, material ni ningún recurso creado en GCP.
**Actualizada el 15/11/2026 con las decisiones del instructor** (D1, D2, D3/D5; D4 y D7 siguen sin respuesta y llevan un supuesto marcado). Los cambios están en §1, §2.1, §2.3, §3.1–§3.2, §6, §8, §9, §10, §11 y en la nueva §12; las tareas nuevas son T27–T36 en [`TAREAS-S3.md`](TAREAS-S3.md).
Sesión: **viernes 20/11/2026, 10:00–14:00 (hora de Perú), 4 horas.** S2 es el miércoles 18/11 y aún no ha ocurrido: S3 se prepara antes. Lo que dependa de lo que pase en S2 lleva la marca **[S2]** y se ajusta el miércoles por la tarde.
Lista de tareas: [`TAREAS-S3.md`](TAREAS-S3.md).

Reglas que rigen todo lo de abajo (decididas el 14–15/11/2026): solo `develop`; no inventar datos ni cifras (tarifas, cuotas, créditos gratuitos, regiones: **«sin verificar»** salvo que se midan; no se citan precios); lo que no se ejecutó de verdad se dice «sin verificar»; sin rutas personales ni correos en nada que se publique; control de costes explícito; cuenta de servicio y secretos con mínimo privilegio y **sin claves JSON** en el repositorio; la autenticación de GitHub Actions con GCP sin claves (Workload Identity) es de **S4**, no de S3.

---

## 1. Objetivo y qué entiende el alumno al terminar

**Objetivo.** Llevar a GCP lo que en S1 y S2 corría «en local» (el *on-premise* simulado): los datos, el servicio y sus secretos, sabiendo qué se mueve, cómo se comprueba que llegó bien y cuánto cuidado de costes hace falta.

Al terminar, la persona asistente puede:
1. Explicar las **fases** de una migración (evaluar, planificar, ejecutar, optimizar) y las tres estrategias que se practican (**rehost, replatform, refactor**), y ubicar cada pieza del caso en el **mapa de equivalencias** (archivos → Cloud Storage; SQLite → BigQuery; `.env` → Secret Manager; imagen → Artifact Registry; `uvicorn` → Cloud Run; logs → Cloud Logging).
2. Hacer un **inventario** de su caso y decidir qué estrategia aplica a cada pieza.
3. Subir los datos originales a Cloud Storage con su huella (SHA-256), cargar las tablas `master_`, `fs_` y `ml_` en BigQuery y **demostrar que coinciden con las de SQLite** (conteos, esquemas, agregados), con una validación que es código y pruebas, no capturas.
4. Explicar por qué una cuenta de servicio con **mínimo privilegio** y un secreto en Secret Manager son mejores que una clave JSON o un `.env` en el repositorio.
5. Publicar la imagen de S2 en Artifact Registry, desplegarla en Cloud Run, **comprobarla** (`/salud`, `/listo`, una predicción, `comparar`) y **leer sus registros** siguiendo un `X-Request-ID`.
6. **Controlar el gasto**: presupuesto y alertas, región y tamaños mínimos, y borrar todo al terminar; y saber que una alerta avisa pero no corta el gasto (comprobarlo en la documentación vigente).
7. Escribir un **plan de rollback** («cómo vuelvo a lo local si falla»).

Lo que **no** entra: autenticación de Actions con GCP (S4), despliegue desde workflow (S4), monitoreo, alertas de operación y rollback de modelos (S5), MLflow en Cloud SQL (solo se menciona, ver §3.3). **La red neuronal (D1) y GKE (D2) no son objetivos obligatorios de la sesión:** son extras al final (§3.1) y no están en el mínimo viable.

**Mensaje honesto que debe quedar claro** (hallazgo de esta planificación): la API de S2 **no lee datos ni usa secretos**: el modelo va dentro de la imagen y solo hay una variable (`CURSO_LOG_NIVEL`). Quien lee datos es la **interfaz** (`ia_mlops/interfaz/`, SQLite montada en solo lectura). Por tanto, desplegar la API en Cloud Run **no «apunta» a BigQuery**; BigQuery recibe una copia analítica validada. Que la interfaz consulte BigQuery sería un refactor que queda fuera de S3 (ver D9).

---

## 2. Qué se reutiliza y qué hay que crear

### 2.1 Se reutiliza
| Pieza | Dónde | Uso en S3 |
|---|---|---|
| API (FastAPI) e imagen `retencion-api` | `04-Proyecto-Base/ia_mlops/api/`, `deploy/docker/Dockerfile` (usuario 10001, puerto 8080, `/salud` y `/listo`, registro JSON por stdout) | Es lo que se publica y se despliega. **No se cambia código**: el registro JSON ya sirve para Cloud Logging |
| Guía «del ordenador al servicio» | `04-Proyecto-Base/docs/del-ordenador-al-servicio.md` y su presentación (S2) | Su apartado 9 («¿ya es producción?») es el punto de partida de la teoría: S3 cierra las filas «S3» de esa tabla |
| Guía de migración | `03-Entorno/guias/migracion-on-premise-a-gcp.md` | Es el esqueleto de la teoría y del laboratorio. **Hay que actualizarla** (§2.3) |
| Laboratorio de Kubernetes | `03-Entorno/guia-docker-kubernetes-gke/` (34 diapositivas, chuleta, 6 ejercicios, kind probado el 13/11/2026), `deploy/kubernetes/` | **Decidido el 15/11/2026 (D2):** el laboratorio kind queda como **autoestudio**; el bloque C (GKE) se replantea **con GCP** como demo documentada **solo del instructor** (§12.2). Hasta que T32 la ejecute, GKE está **sin ejecutar** |
| Taller de punta a punta (café CQI) | `taller-ml-ia-dev-production/` | Práctica **previa** de despliegue: publica `cafe-api` y `cafe-interfaz` en **GHCR** desde un workflow con aprobación. Sirve de antecedente («publicar una imagen versionada ya lo hiciste») y de **plan B** si un alumno no tiene imagen propia: la baja de GHCR y la sube a Artifact Registry. `docker pull` desde GHCR en un Codespace está **sin verificar** (lo dice su guía) |
| Caso propio | `02-Proyecto-Transversal/alumno/` (hoja, plantilla y rúbrica de avance) | La tarea de S3 **es el avance 3**. Hay que concretar su técnica (§2.3) |
| Patrón de sesión completa | `01-Sesiones/S2-API-y-Docker/` | Mismos componentes, marco de presentación y pruebas |
| Recap | `01-Sesiones/recap/recap-01/` | Formato de `recap-02` |
| Índices y PDF | `00-Planificacion/indices-de-sesion/contenido_indices.py`, `00-Planificacion/pdfs/contenido_pdfs.py` | Alta de S3 y `recap-02` |
| Datos de la demo | `04-Proyecto-Base/data/raw/muestra_online_retail_ii.csv` (≈2 MB, 23 070 filas) y `data/processed/curso.db` (≈7,5 MB; `raw_`, `master_`, `fs_`, `ml_`) | La demo usa la **muestra**, no el Excel de 45 MB: menos tiempo y menos coste, mismo mensaje. Licencia CC BY 4.0 (comprobada en el curso) |

### 2.2 Qué hay que crear
**Material de la sesión** (carpeta `01-Sesiones/S3-Despliegue-y-Redes-Neuronales/`): presentación, guion, checklist, teoría y glosario, guía de laboratorio replicable, tarea, rúbrica, plantilla de evidencia (§4).

**Código y scripts** (los nombres son propuestos; ninguno existe):
- `04-Proyecto-Base/ia_mlops/migracion/` (Python, parametrizado por ruta de SQLite, prefijos y carpeta de salida; sirve para Retail y para Bank Marketing sin cambios):
  `inventario.py` (archivos, tablas con filas y columnas, variables de entorno/secretos detectados, servicios e imágenes → `inventario.md` y `.json`),
  `exportar.py` (SQLite → Parquet por tabla + `esquema.json` + `conteos.json` + `MANIFEST.sha256`),
  `validar.py` (conteos, esquemas con tabla de equivalencia de tipos, agregados y nulos por columna, comparación de una muestra de filas; sale con código distinto de 0 si algo no coincide; admite como destino BigQuery **o una carpeta/DuckDB para el ensayo local**).
- `04-Proyecto-Base/deploy/gcp/` y `deploy/cloud-run/` (bash; hoy `deploy/cloud-run/` solo tiene `.gitkeep`): `env.ejemplo.sh` (variables; sin valores reales), `preparar_proyecto.sh` (APIs), `datos.sh` (bucket, subida, dataset, carga), `secretos_y_cuenta.sh`, `imagen.sh`, `desplegar.sh`, `probar.sh`, `limpiar.sh`. **Todo script que crea algo corre en modo «mostrar qué haría» por defecto** y exige `--ejecutar`; `limpiar.sh` exige `--confirmar`.
- `04-Proyecto-Base/tests/test_migracion.py` (sin GCP: ver §4) y pruebas estáticas de los scripts.
- Un recap: `01-Sesiones/recap/recap-02/`.

**Capturas y salidas reales de la demo** (§7). Sin ellas, la guía de laboratorio no se puede cerrar: **no se escriben salidas esperadas inventadas**.

### 2.3 Qué hay que corregir o completar en lo existente
- `migracion-on-premise-a-gcp.md`: su paso 2 habla de `MANIFEST.sha256` en `data/raw`, **que no existe** en `04-Proyecto-Base` (en el caso del alumnado la huella está en `02-Proyecto-Transversal/datos/SHA256SUMS`). Hay que generar el manifiesto (lo hace `exportar.py`) y dejar el texto coherente. Cloud Storage informa de MD5 y CRC32C, no de SHA-256 (comprobar en la documentación vigente): por eso la verificación de integridad es «descargar y comprobar el SHA-256» o guardar el SHA-256 como metadato propio.
- La guía dice «6. desplegar en Cloud Run apuntando a los datos migrados»: se reescribe según el hallazgo del §1.
- `rubrica-avance.md` (fila del avance 3: «Se concretará al preparar S3») y `plantilla-avance.md` (apartado del avance 3), y el apartado 9 de la hoja del caso: se concretan en la tarea S3 (T17). La rúbrica **conserva los pesos 20/40/40**.
- `requirements`: `pyarrow` **no figura** en `requirements-api.txt` ni en `pyproject.toml` del proyecto base. Hay que comprobar si `env-ia-mlops` lo trae (T03); si no, decidir entre añadirlo o exportar a CSV con esquema explícito (D8).
- `devcontainer`: el Codespace no trae `gcloud` (hoy trae Docker, kind y kubectl). **D5 decidida el 15/11/2026: la demo es en Codespaces**, así que hay que preparar un `.devcontainer` con el SDK de Google Cloud (T34), una guía de instalación y autenticación para el alumno (T35) y una prueba real única (T36). Ver §12.3.

---

## 3. Reparto de las 4 horas

### 3.1 Propuesta (ajustada ligeramente respecto a la del instructor) y justificación
| Hora | Min | Bloque | Contenido | Material |
|---|---|---|---|---|
| 0:00–0:15 | 15 | **Recap-02 y estado del grupo** | 10 min de S2 en cinco minutos ampliados (API, contrato, 422/503/500, imagen, contenedores, interfaz, dos contenedores, taller) + 5 min de pregunta de mano alzada: quién tiene proyecto de GCP, facturación activada y la imagen de S2 construida (los que no, siguen en modo «solo mirar» y usan el plan B de D7) | `recap-02/index.html` |
| 0:15–0:55 | 40 | **Teoría de migración** | Fases, las tres «R» y las otras tres (se mencionan), mapa de equivalencias, inventario, **riesgos de costes, datos e identidad**, IAM y mínimo privilegio, regiones, rollback | presentación diap. 3–14, `teoria/README.md` |
| 0:55–1:45 | 50 | **Demo 1 · datos** | Inventario → bucket → subida con huella → exportación a Parquet → carga en BigQuery → **validación** (la parte que se vuelve `pytest`) | demo en vivo + capturas de respaldo |
| 1:45–2:00 | 15 | **Pausa** | | |
| 2:00–3:00 | 60 | **Demo 2 · servicio** | Secret Manager → cuenta de servicio mínima → Artifact Registry y `docker push` → Cloud Run privado → comprobar (`proxy`, `comparar`) → registros → una segunda revisión y vuelta atrás → **cómo se borra** | demo en vivo + capturas |
| 3:00–3:30 | 30 | **Extra (colchón con orden de prioridad; reparto de minutos = propuesta)** | 1.º **Costes y limpieza obligatoria** (≈10 min, en vivo, sobre lo que se creó) · 2.º **Puente a GKE** (≈12 min: mapa «Cloud Run frente a GKE» con diapositivas; la **demo de GKE la hace solo el instructor, documentada** con las salidas del ensayo T32, y se ejecuta en vivo **solo si hay tiempo**; todo lo creado se elimina al cerrar) · 3.º **Red neuronal como último extra** (≈8 min, solo si queda tiempo: se enseña lo ya entrenado y registrado, **sin entrenar en vivo**; si no, autoestudio) (D1, D2) | presentación; `guia-docker-kubernetes-gke` bloque C; material de T27–T33 |
| 3:30–4:00 | 30 | **Tarea y cierre** | Tarea = avance 3, plantilla de evidencia, rúbrica, qué hacer primero en casa (proyecto, presupuesto, `gcloud auth`), cómo no gastar, adelanto de S4 (Workload Identity) | presentación diap. final, `tarea/README.md` |
| | **240** | | | |

**Qué se hace en vivo y qué queda de autoestudio (el tiempo es una propuesta, se ajusta con el ensayo T23).** Las cuatro horas siguen sumando 240; solo cambia el contenido del extra de 30 min.
- **En vivo, siempre:** costes y limpieza obligatoria (1.º del extra).
- **En vivo si hay tiempo, y si no, con capturas o salidas documentadas:** puente a GKE y demo del instructor (2.º). La demo la ejecuta **solo el instructor**; el alumno **no** crea clústeres. Si se hace en vivo, el clúster se borra **antes de terminar la sesión**.
- **En vivo solo si sobra tiempo:** la red neuronal (3.º), enseñando lo ya entrenado, registrado y empaquetado; **no se entrena en vivo**.
- **Autoestudio (con guía):** laboratorio kind completo, «cómo se rompe» (permiso denegado, 503 en Cloud Run, bucket de otra región; pasa a la guía de laboratorio) y la red neuronal completa si no cupo.
- **Fuera del mínimo viable:** la red neuronal y GKE (se puede entregar S3 completa sin ellas).

Por qué así:
- **Recap 15 y no menos:** S2 acaba de ocurrir el miércoles y el avance 2 se entrega el mismo viernes a las 10:00; hace falta recordar contrato y contenedor porque la demo parte de esa imagen, y averiguar en el momento quién se queda sin proyecto de GCP para no descubrirlo a la hora 2.
- **Teoría 40 y no 60** (como en S1 y S2): el contenido es más corto y la demo es la parte que enseña; la teoría es el mapa y el vocabulario.
- **Demo 1 más corta (50) que Demo 2 (60):** los datos son pasos repetitivos con una pieza difícil (la validación); el servicio tiene más piezas nuevas (identidad, secreto, registro, Cloud Run) y la parte de «leer registros» merece tiempo.
- **Extra 30 como colchón, no como contenido fijo:** hoy nada de GCP se ha ejecutado; las demos reales casi siempre se alargan. Si no hay colchón, se recorta Kubernetes primero y después el «cómo se rompe».
- **La replicación del alumno ocurre después**, en su cuenta (decisión del instructor): por eso no hay bloque de práctica guiada de 2 horas como en S1 y S2. A cambio, la guía de laboratorio tiene que poder seguirse sin el instructor. Entre S3 (vie 20) y la entrega del avance 3 (mié 25, 10:00) hay cinco días: es el margen para replicar.
- **Total 240**, igual que S1 y S2; una prueba debe vigilar que los minutos de la presentación suman 240.

### 3.2 Si el tiempo se descontrola
Recortar en este orden: red neuronal (pasa a autoestudio) → demo de GKE en vivo (se enseñan las salidas documentadas del ensayo) → puente a Kubernetes → «cómo se rompe» (ya es autoestudio) → la segunda revisión y el rollback → la comparación `comparar` contra el servicio en Cloud Run (queda `/listo` y una predicción). **No se recorta nunca:** la validación de la migración, el mínimo privilegio, el plan de costes y la limpieza.

### 3.3 Lo que solo se menciona
MLflow en Cloud SQL y Cloud Storage (frente a Vertex AI Experiments/Registry), Cloud Scheduler, Vertex AI Pipelines, Cloud Composer y Cloud Build: salen en el mapa de equivalencias, sin práctica. En S4 el pipeline lo orquesta GitHub Actions.

---

## 4. Componentes de la sesión (mismo patrón que S2)

Carpeta de destino: `01-Sesiones/S3-Despliegue-y-Redes-Neuronales/` (los nombres de carpeta ya existen: `evidencias/`, `practica/`, `tarea/`, `teoria/`; falta `slides/`).

| # | Componente | Archivo | Contenido y criterio de «hecho» |
|---|---|---|---|
| 1 | **Presentación** | `slides/index.html` | Marco, paleta, teclas (flechas, O índice, S notas, F pantalla completa) y reloj de minutos de S2; minutos por diapositiva que suman 240; notas del ponente; diagramas simples (mapa on-premise → GCP, flujo de datos SQLite → GCS → BigQuery, identidad mínima, del `docker push` a Cloud Run); capturas reales de la demo; sin recursos externos. Sobrio, nada recargado |
| 2 | **Guion con tiempos** | `guion.md` | Tabla por bloque como la de S2; qué se ejecuta en directo y qué se enseña con capturas; «si algo falla en directo» (permiso denegado, API no habilitada, cuota, Docker sin sesión, tiempo de despliegue); qué se dice como **comprobado** y qué como **sin verificar** |
| 3 | **Checklist** | `checklist.md` | Docente (proyecto de demo listo, presupuesto, APIs, imagen construida, sesión de `gcloud`, capturas de respaldo abiertas, recursos antiguos borrados) y alumnado (antes: cuenta, proyecto, facturación o plan B; durante; después: limpieza hecha y comprobada) |
| 4 | **Teoría y glosario** | `teoria/README.md` | Fases, estrategias, mapa, inventario, IAM, secretos, regiones, costes y límites de lo que se afirma. Glosario: bucket, dataset, tabla, job de carga, Parquet, repositorio, imagen, revisión, cuenta de servicio, rol, secreto y versión, registro, presupuesto |
| 5 | **Guía de laboratorio replicable** | `practica/guia-laboratorio.md` | Pasos numerados con presupuesto de tiempo, **dónde ejecutar** (D5), orden exacto de scripts, «qué debes ver» (salidas **reales** de la demo), «si falla», costes de cada paso, limpieza al final. Debe poder seguirse sin el instructor |
| 6 | **Scripts gcloud/bq** | `04-Proyecto-Base/deploy/gcp/`, `deploy/cloud-run/` | Ver §2.2. Parametrizados (`PROYECTO`, `REGION`, `PREFIJO`); sin valores personales; sin claves; etiqueta `curso=ml-ia` en todo lo que se crea |
| 7 | **Scripts de exportación, carga y validación** | `04-Proyecto-Base/ia_mlops/migracion/` | SQLite → Parquet → Cloud Storage → BigQuery con comprobación de **conteos y esquemas** (y agregados y nulos). Probados en local con carpeta/DuckDB como destino sustituto y, en la demo, con BigQuery real |
| 8 | **Plantilla de evidencia** | `evidencias/plantilla-migracion-gcp.md` | Inventario; estrategia por pieza; datos (qué subí, huella, conteos, esquemas); identidad (cuenta de servicio, roles y por qué); secreto; imagen (nombre, etiqueta, resumen); servicio (región, tamaño, privado); pruebas del servicio; registros (sin datos del cliente); **costes: lo que vi en la consola**; rollback; limpieza (listados vacíos); qué no pude ejecutar; ayuda recibida |
| 9 | **Tarea** | `tarea/README.md` | «Migrar el caso propio (Bank Marketing) a GCP y desplegar el servicio.» **Es el avance 3.** Pasos, evidencia mínima, honestidad, ruta sin facturación (D7) |
| 10 | **Rúbrica** | `tarea/rubrica.md` | **20/40/40** (reproducibilidad / técnica / análisis y decisión), igual que S1, S2 y la rúbrica de avance (comprobado). Topes propuestos: clave JSON o credencial en el repositorio → técnica ≤ 25; recursos sin borrar o sin presupuesto → análisis ≤ 25 (propuesta); servicio público sin motivo → técnica ≤ 30; solo capturas → reproducibilidad ≤ 8; presentar como ejecutado lo que no se ejecutó → análisis ≤ 20; migración sin validación de conteos y esquemas → técnica ≤ 25 |
| 11 | **Recap-02** | `01-Sesiones/recap/recap-02/` | `index.html` (≈12 diapositivas, mismo marco y formato que recap-01), `README.md`, `guion-profesor.md`. Contenido: S2 en cinco minutos: del modelo al servicio; contrato que sale de la firma; 200/422/503/500 y rechazar frente a avisar; vivo frente a listo; registro JSON con id; imagen y contenedor (usuario 10001); interfaz y dos contenedores; taller de punta a punta; autoevaluación de 5–6 preguntas; puente a S3. **Se ajusta tras S2 [S2]**. Actualizar la tabla de `recap/README.md` («Pendiente» → «Hecho») |
| 12 | **Índices** | `00-Planificacion/indices-de-sesion/contenido_indices.py` | Alta de los enlaces de S3 (componentes de la lista `COMPONENTES`), `recap-02` enlazado desde S3 (como recap-01 desde S2), estado «Material preparado» solo cuando sea cierto; regenerar y pasar `test_indice.py` |
| 13 | **PDF** | `00-Planificacion/pdfs/contenido_pdfs.py` | Elementos de S3 (presentación, teoría, guía, tarea, rúbrica, evidencia, checklist; para el instructor, README y guion) y, si procede, `recap-02` (recap-01 sigue sin PDF); regenerar y pasar `test_pdfs.py` |
| 14 | **Pruebas** | `04-Proyecto-Base/tests/` y pruebas de la presentación | (a) migración **sin GCP**: `exportar` produce Parquet con los conteos de SQLite; `validar` pasa con la copia fiel y **falla** si se borra una fila, se cambia un tipo, se altera un valor o falta una tabla (roturas deliberadas, como en S2); (b) estáticas de los scripts: sin claves ni correos ni IDs de proyecto reales, toda creación con etiqueta, `limpiar.sh` cubre todo lo que se crea, ningún script «borra todo» sin `--confirmar`; (c) presentación: minutos = 240, sin recursos externos, marco; (d) una marca `gcp` para lo que necesita la nube (se omite por defecto, nunca falla en CI) |

---

## 5. Diseño técnico de la demo

La demo la ejecuta **solo el instructor, con la cuenta del profesor**. Se hace con el caso del instructor (Online Retail II, muestra del curso); el alumno replica con **su caso** (Bank Marketing) en **su** cuenta. Los nombres de los scripts sirven para los dos.

### 5.1 Proyecto y parámetros
Un **proyecto dedicado y desechable** para la demo (se puede borrar entero al final: es la limpieza de último recurso). Nombre del proyecto genérico, sin datos personales ni de empresa. Variables (en `env.ejemplo.sh`; cada persona copia a `env.sh`, que va en `.gitignore`):

| Variable | Qué es | Valor |
|---|---|---|
| `PROYECTO` | ID del proyecto | lo da GCP al crearlo; no se escribe en el repositorio |
| `REGION` | una sola región para todo | ver D4 |
| `PREFIJO` | prefijo de nombres | `curso-ml` |
| `BUCKET` | `${PROYECTO}-${PREFIJO}-datos` | el ID del proyecto en el nombre ayuda a que sea único (comprobar al crear) |
| `DATASET` | conjunto de datos de BigQuery | `curso_ml` (BigQuery admite guion bajo, no guion) |
| `REPO_AR` | repositorio de imágenes | `curso-imagenes` |
| `IMAGEN` / `ETIQUETA` | nombre y versión | `retencion-api` / etiqueta explícita (huella o `s3-1`); **no se despliega por `latest`** |
| `SERVICIO` | servicio de Cloud Run | `retencion-api` |
| `CUENTA_SERVICIO` | identidad de ejecución | `sa-retencion-api` |
| `SECRETO` | nombre del secreto | `curso-demo-secreto` |

Toda creación lleva la etiqueta `curso=ml-ia` donde el servicio la admite, para localizar y borrar.

### 5.2 Servicios, en orden, y qué se comprueba
Se habilitan **solo** las APIs necesarias (Storage, BigQuery, Artifact Registry, Cloud Run, Secret Manager, IAM, y las que pida cada orden; comprobar la lista real en T08). Habilitarlas se hace **antes** de la clase (tarda) y se enseña en una captura.

| Paso | Qué se hace | Se comprueba con | Estrategia |
|---|---|---|---|
| 0 | Presupuesto y alertas; APIs | captura de la consola de Facturación; `gcloud services list --enabled` | Nuevo |
| 1 | **Inventario** | `inventario.py` → `inventario.md` | Evaluar |
| 2 | **Bucket**: región única, acceso uniforme a nivel de bucket, **prevención de acceso público**, versionado de objetos, etiqueta, caducidad opcional de lo temporal | `gcloud storage buckets describe` | Replatform |
| 3 | Subir `data/raw` (muestra) y el `MANIFEST.sha256` | descarga a una carpeta temporal y `sha256sum -c`; recuento de objetos | Replatform |
| 4 | **Exportar** `master_*`, `fs_*`, `ml_*` a Parquet con `exportar.py` y subirlos a `gs://…/parquet/` | `conteos.json`, `esquema.json` | Replatform |
| 5 | **Dataset de BigQuery** en la **misma ubicación** que el bucket (necesario para cargar desde él; comprobar en la documentación vigente) y con caducidad por defecto de las tablas (valor puesto por nosotros, no una cifra de Google) | `bq show` | Replatform |
| 6 | **Carga** `bq load --source_format=PARQUET` por tabla | `bq show` (filas, esquema) | Replatform |
| 7 | **Validación** `validar.py` contra BigQuery: conteos, esquemas (con la tabla SQLite → BigQuery), agregados (suma, mínimo, máximo y nulos por columna numérica; distintos en las claves), muestra de filas. Las consultas llevan **`--dry_run` primero y `--maximum_bytes_billed`** como tope | `validacion.json` + código de salida | Evaluar/Ejecutar |
| 8 | **Secret Manager**: un secreto con **valor de ejemplo no sensible** (generado al azar, sin significado real) y una versión | `gcloud secrets versions list` (nunca se imprime el valor) | Replatform |
| 9 | **Cuenta de servicio de ejecución** `sa-retencion-api` **sin claves**, con **un solo permiso**: acceso al valor de **ese** secreto (concedido sobre el secreto, no sobre el proyecto). No se le dan roles de Storage ni de BigQuery porque la API no los usa (se enseña como principio: lo que no se necesita no se concede) | `gcloud secrets get-iam-policy`; `gcloud projects get-iam-policy` filtrando por la cuenta (debe salir vacío) | Refactor |
| 10 | **Artifact Registry**: repositorio Docker en `REGION`; `gcloud auth configure-docker` (helper de credenciales, sin clave en disco); `docker tag` y `docker push` de la imagen de S2 construida en el Codespace | `gcloud artifacts docker images list` (con resumen/digest) | Rehost |
| 11 | **Cloud Run**: `gcloud run deploy` con la imagen **por etiqueta fijada** (o resumen), la cuenta del paso 9, el secreto como variable de entorno, **sin acceso público (`--no-allow-unauthenticated`)**, **mínimo de instancias 0**, **máximo de instancias bajo**, memoria y CPU **medidas** antes (`docker stats` del contenedor local; no se adivinan), puerto 8080 y `CURSO_LOG_NIVEL=INFO` | `gcloud run services describe` | Rehost |
| 12 | **Probar**: `gcloud run services proxy` (pone un puerto local con tu identidad, **sin tocar el código** de la API ni exponerla) y sobre él `/salud`, `/listo`, `/modelo`, una predicción con `tests/datos/cliente_ejemplo.json` y `python -m ia_mlops.modeling.comparar --url http://127.0.0.1:<puerto>`. Esperado: la misma probabilidad que en local (con la muestra, `0.8278889191932133`; los últimos decimales pueden variar) y diferencias cero. El puerto local debe evitar el 8080 si ya está ocupado | salida de `comparar` | — |
| 13 | **Registros**: `gcloud run services logs read` y `gcloud logging read` filtrando por servicio; en la consola, Logs Explorer. Se sigue un `X-Request-ID` desde la petición hasta su línea JSON; se comprueba que **ninguna línea lleva datos del cliente**; se provoca un 422 con el caso 01 de `tests/datos/casos/` y se localiza su línea | captura + comando | Replatform |
| 14 | **Segunda revisión y vuelta atrás**: cambiar una variable de entorno, ver la revisión nueva y devolver el tráfico a la anterior (rollback del servicio) | `gcloud run revisions list` | Refactor |
| 15 | **Plan de rollback hacia lo local** (documento: la imagen y los datos siguen en local; cómo volver) | texto | Planificar |
| 16 | **Limpieza** con `limpiar.sh` y verificación con listados vacíos; opcionalmente, borrar el proyecto | `gcloud … list` por servicio | Optimizar |

Qué usuario/rol/cuenta: el **instructor** actúa como propietario de su proyecto de demo (es su cuenta de profesor y su proyecto desechable); eso se **dice en voz alta** como excepción de la demo. El **servicio** corre con una cuenta de servicio propia de un solo permiso. En la guía del alumno se pide lo mismo: tu proyecto, tu usuario propietario, y la cuenta de servicio mínima para el servicio. Cargas con cuenta de servicio y suplantación (`--impersonate-service-account`) se mencionan como mejora, sin práctica.

### 5.3 Lo que se afirma y lo que no
Todo lo anterior son **órdenes y opciones de la documentación de Google, aún no ejecutadas**. Nombres exactos de opciones y de roles se confirman con `gcloud … --help` y con la documentación vigente durante T08–T10. Nada de precios, créditos gratuitos, cuotas ni límites gratuitos se escribe (la búsqueda web está bloqueada): se dice «consulta la página de precios y la consola de facturación; sin verificar aquí».

---

## 6. Dónde se ejecuta (para la demo y para el alumno)
Windows no es el entorno de los scripts: son `bash` y Python. Se ejecutan en el **Codespace del curso** (mismo entorno que S2, con Docker) (decidido el 15/11/2026, D3/D5: la demo es en Codespaces) y **Cloud Shell queda como plan B**. El Codespace necesita el SDK de Google Cloud preparado (T34, §12.3). La orden de PowerShell/CMD equivalente **no se escribe** (sin probar): quien trabaje en Windows usa el Codespace.

---

## 7. Cómo se captura la demo

1. **Navegador de capturas:** el Chrome de capturas del curso. **El instructor inicia sesión él mismo** en la consola de GCP y en GitHub; **nunca se escriben ni se piden credenciales, códigos ni tokens** en ningún script, mensaje o archivo.
2. **Qué se captura:** (a) la **consola de GCP** (Facturación → presupuesto; Cloud Storage; BigQuery con el esquema y el número de filas; Artifact Registry; Secret Manager; IAM; Cloud Run con revisión y registros; Logs Explorer); (b) la **terminal** (Codespace en el navegador o Cloud Shell) con la orden y su salida real.
3. **Quién ejecuta qué:** las órdenes que **crean** recursos las ejecuta el instructor, o las **autoriza expresamente** (una a una) para que las ejecute el asistente. Las que solo **leen** (`list`, `describe`, `logs read`) pueden prepararse en lote. El asistente nunca abre sesión por su cuenta.
4. **Cada captura** va con: la orden exacta, la hora, la versión de `gcloud` (`gcloud version`) y un nombre de archivo estable que usan la guía y las diapositivas. Las salidas de texto se guardan también en `salidas-reales-gcp.json` (como `salidas-reales.json` en S2).
5. **Privacidad antes de publicar (T12):** recortar o tapar el **correo de la cuenta** (arriba a la derecha de la consola), el **identificador de la cuenta de facturación**, el número de proyecto si aparece en URLs, y **cualquier token** (no se imprime nunca el token de identidad: se usa en línea dentro de la orden). Buscar en el texto y en las imágenes. Ningún dato personal: «la cuenta del profesor».
6. **Ensayo antes de la clase y en vivo el viernes:** una ejecución completa el **martes 17/11** produce las capturas y las salidas reales (y los tiempos), y el viernes se repite en vivo con **las capturas como respaldo** si falla la red, la consola o un servicio. Los dos ensayos cuestan: el segundo usa nombres nuevos y se borra al acabar la clase.
7. Lo que **no se llegue a ejecutar** se escribe como «sin verificar» en la guía, la presentación y el índice, con la orden tal como figura en la documentación.

---

## 8. Plan de limpieza y de costes

**Principios.** Todo lo creado lleva `curso=ml-ia`. Una región. Tamaños mínimos. Nada público. Nada que escale solo (mínimo de instancias 0, máximo bajo). Tablas con caducidad. El presupuesto se crea **antes** que cualquier recurso.

**Antes de crear nada (alumno y profesor):** proyecto nuevo y desechable; **presupuesto con alertas** (importe pequeño elegido por cada persona, con avisos por umbrales); confirmar en la documentación vigente **qué hace y qué no hace** una alerta (el curso asume que **avisa, no corta el gasto**: comprobarlo); mirar la consola de facturación al terminar cada bloque.

**Durante:** un solo servicio, una sola imagen, un solo bucket; no repetir cargas; las consultas de validación con `--dry_run` y tope de bytes.

**Al terminar (siempre, el mismo día):** `limpiar.sh` (lista lo que va a borrar; con `--confirmar` lo borra: servicio de Cloud Run, repositorio de imágenes, secreto, cuenta de servicio, dataset, bucket, en ese orden), y después los **listados de comprobación** (todos vacíos). Si hay dudas: **borrar el proyecto entero** (los recursos dejan de cobrar al apagarse el proyecto; confirmar el plazo de recuperación en la documentación). Anotar en la evidencia lo que mostró la consola de facturación, **sin cifras inventadas**: solo lo que se vea.

**Cobros posibles que hay que vigilar y no se cuantifican aquí:** almacenamiento en bucket y en Artifact Registry (las imágenes de cientos de MB se acumulan), consultas y almacenamiento de BigQuery, instancias de Cloud Run, versiones de secretos y salida de red entre regiones. Cada una se marca «sin verificar» hasta mirarla en la consola real.

**GKE (decisión D2 del 15/11/2026): lo crea y lo borra solo el instructor.** Al cerrar la práctica se **elimina TODO** lo que GKE haya creado, para evitar gastos inesperados: el clúster y sus grupos de nodos, los **discos** (incluidos los persistentes que queden huérfanos), los **balanceadores** y reglas de reenvío, las **direcciones IP** reservadas y las imágenes o repositorios que solo servían para esta demo. `limpiar.sh` debe cubrirlo (T33), con listados de comprobación vacíos, y al día siguiente se mira la consola de Facturación (lo que se vea, sin cifras inventadas; el retraso con el que aparecen los cargos está **sin verificar**). Ningún alumno crea recursos de GKE en el camino obligatorio.

**Cómo se evita que el alumno gaste sin querer:**
1. Scripts en modo «mostrar» por defecto (`--ejecutar` explícito) y un `limpiar.sh` con `--confirmar`.
2. La guía **empieza** por proyecto, presupuesto y limpieza, y **termina** con los listados vacíos; la evidencia **exige** pegarlos.
3. Valores por defecto seguros: privado, mínimo de instancias 0, máximo bajo, caducidad de tablas.
4. Nada de GKE, Cloud SQL, máquinas virtuales ni clústeres en el camino obligatorio **del alumno** (GKE solo existe en la demo del instructor, y se borra).
5. Sin facturación activada, la ruta sin nube (D7); nadie está obligado a pagar.
6. Una prueba estática vigila que la guía y los scripts no contengan recursos fuera de la lista permitida.
7. La rúbrica penaliza dejar recursos vivos o no tener presupuesto.

---

## 9. Riesgos y qué queda «sin verificar» si no se llega a ejecutar

| Riesgo | Efecto | Mitigación |
|---|---|---|
| La cuenta del profesor no puede crear proyecto o facturación a tiempo (T08) | Todo [GCP] se retrasa | T08 es lo primero y no depende de nada; plan B: solo ensayo local + guía con órdenes «sin verificar» |
| Una API o cuota bloquea una orden | Una demo se corta | Habilitar APIs antes; capturas de respaldo; guion con la tabla «si falla» |
| La red corporativa/proxy del portátil rompe `gcloud` o `docker push` | Demo en directo caída | Ejecutar desde el Codespace en el navegador o Cloud Shell, no desde el portátil |
| `docker push` lento (imagen de unos cientos de MB) | Se come el bloque | Empujar la víspera y el viernes solo enseñar; tiempo medido en el ensayo (T10) |
| Región sin algún servicio | Orden fallida | Elegir tras listar ubicaciones reales (D4) |
| El alumno no tiene facturación | No puede replicar | D7 |
| Se crean recursos y se olvidan | Coste | §8 |
| `pyarrow` ausente | Exportar falla | T03 lo decide (D8) |
| Capturas con datos personales | Fuga al publicar | T12 |
| S2 revela problemas de Docker o Codespace en el grupo | Menos gente con imagen propia | [S2] plan B de la imagen (GHCR del taller) y modo «solo mirar» |
| Sesión muy densa | Se corta la validación | §3.2: lo que no se recorta |
| El `.devcontainer` con el SDK falla o tarda demasiado al reconstruir el Codespace (cuota de horas escasa) | La demo en Codespaces cae y no hay segunda prueba | T34 compara formas de instalación antes; T36 es **una sola** prueba larga el martes; plan B dentro del mismo Codespace (script de instalación) y Cloud Shell |
| Se agotan las horas de Codespaces antes del viernes | Sin ensayo ni demo en Codespaces | Una sola prueba (T36), parar el Codespace al terminar cada tramo, no usar Codespaces para T23; cuota vigente **sin verificar** (mirarla en la cuenta) |
| Se queda un clúster, disco, balanceador o IP de GKE vivo | Gasto inesperado | T33 (`limpiar.sh` y listados vacíos) antes de crear nada; revisión de Facturación al día siguiente; T26 lo comprueba el viernes |
| El extra de la red neuronal no cabe (peso de `torch`, descarga del dataset, tiempos) | No hay extra | T27 (pico técnico) decide con medidas; alternativas ONNX Runtime o MLP de scikit-learn; si no cabe, autoestudio posterior. No afecta al mínimo viable |

**Sin verificar si no se ejecuta:** toda orden de `gcloud`/`bq`/`docker push`, los nombres de roles y opciones, las ubicaciones disponibles, el comportamiento del presupuesto, la carga de Parquet a BigQuery y los tipos resultantes, `gcloud run services proxy` y `comparar` sobre él, los tiempos, y cualquier coste. Lo que **sí** quedará verificado sin GCP: los scripts de exportación y validación en local (SQLite → Parquet → destino local), las pruebas y las roturas deliberadas.

---

## 10. Decisiones pendientes (con opciones y recomendación)

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| **D1** · **RESPONDIDA 15/11/2026: (a) reformulada.** La red neuronal **se queda como EXTRA al final de S3** (no obligatorio; el instructor aún piensa el contenido exacto). Va tras un pico técnico previo (T27) y no entra en el mínimo viable. Ver §12.1 | **Red neuronal opcional con PyTorch:** ¿entra como extra de S3 o se deja fuera? | (a) Extra de 30 min en S3; (b) fuera de S3, queda como módulo opcional de autoestudio (`05-Modulo-Redes-Neuronales/`, hoy sin contenido); (c) eliminar | **(b) Fuera de S3.** No hay material, la demo de GCP ya es densa y arriesgada, el programa dice «opcional», y el curso decidió no depender de GPU (`decisiones-y-pendientes.md`), así que no hay prueba cloud preparada para ella. Si el instructor la quiere, que sea un módulo posterior con su propia planificación |
| **D2** · **RESPONDIDA 15/11/2026:** Kubernetes **con GCP (GKE)**, demo solo del instructor, documentada y con todo lo creado eliminado al cerrar; kind como autoestudio. Pendiente: tipo de cluster (§12.2). | **Kubernetes «si hay tiempo»** | (a) 10 min de puente en el extra (mapa «Cloud Run frente a GKE», bloque C de la guía) y el laboratorio kind como autoestudio opcional; (b) laboratorio kind completo en clase; (c) quitarlo | **(a).** El laboratorio está probado pero no cabe sin romper lo esencial; GKE sigue sin ejecutar y no se enseña como hecho |
| **D3** · **RESPONDIDA 15/11/2026 en cuanto al lugar:** la demo es en **Codespaces** (Cloud Shell = plan B). «En vivo con capturas de respaldo» se mantiene como propuesta, sin objeción. | **Demo en vivo o solo con capturas** | (a) Vivo con capturas de respaldo; (b) solo capturas | **(a)**, con ensayo el martes 17. Si el martes algo importante falla, pasar a (b) y decirlo |
| **D4** · **SIN RESPUESTA (15/11/2026)** | **Región** (todo en una) | Candidatas: una de Sudamérica (más cerca de Perú) o una de EE. UU. | Criterios: ubicación del bucket = ubicación del dataset de BigQuery; que **todos** los servicios usados estén en ella; cercanía a Perú. **No se afirman precios ni gratuidad de ninguna.** Decidir tras listar ubicaciones reales en T08 y anotar «sin verificar» lo que no se pueda comprobar. Aviso: las guías del curso usan `us-central1` solo como **ejemplo** de la documentación de Google |
| **D5** · **RESPONDIDA 15/11/2026:** (a) **Codespaces**, con Cloud Shell como plan B. Cómo se instala el SDK (devcontainer o script) se decide en T34, no se da por sabido. Ver §12.3 | **Dónde ejecutan el alumno y el instructor** | (a) Codespace del curso + `gcloud` instalado por un script; (b) Cloud Shell (viene con `gcloud`; hay que traer el repositorio y los datos, y no tiene `env-ia-mlops`); (c) terminal local | **(a), con (b) como plan B.** Mismo Docker y entorno de S2, un solo sitio. Hay que probar el inicio de sesión de `gcloud` en un Codespace (flujo sin navegador local) y decidir si va en el `devcontainer` o en un script aparte |
| **D6** | **Peso de la tarea y del avance 3** | La tarea S3 = avance 3 (ya así en la hoja) | Mantener; cuidar que sea hacedero en cinco días y que la rúbrica diga qué es mínimo |
| **D7** · **SIN RESPUESTA (15/11/2026). SUPUESTO por defecto: «ruta sin nube con ensayo local»** | **Alumno sin facturación activada** | (a) Ruta sin nube: ensayo local completo (Parquet y DuckDB/carpeta) con todos los scripts, y el resto **documentado como «sin ejecutar»**; (b) modo de pruebas de BigQuery sin facturación (existe; sus límites y vigencia **sin verificar**); (c) cuenta de un compañero | **(a) como ruta mínima válida, (b) si se verifica.** Nunca (c) con credenciales ajenas. La rúbrica no penaliza la falta de nube si se declara con claridad; sí penaliza fingirla |
| **D8** | **Formato de exportación** | Parquet (conserva tipos; requiere `pyarrow`) o CSV con esquema explícito | **Parquet** si `pyarrow` está o se añade sin romper nada de S1–S2; si no, CSV con esquema |
| **D9** | **Que la interfaz lea BigQuery** | (a) No: BigQuery es copia analítica validada; (b) sí, como refactor opcional | **(a).** Es una decisión de diseño que se explica: en S3 se migran datos y servicio por separado |
| **D10** | **Secreto de la demo** (la API no usa ninguno) | (a) Valor de ejemplo no sensible montado como variable; (b) cambiar la API para que lo use | **(a).** No se toca el código; el mecanismo se aprende igual y se declara que el servicio actual no lo consume |
| **D11** | **Imagen del alumno** | Su imagen del avance 2; plan B: la imagen del taller (GHCR) bajada y resubida | Confirmar tras S2 qué fracción tiene imagen |
| **D12** | **Dos ejecuciones (martes y viernes) frente a una** | Dos | Dos: el coste es pequeño frente al riesgo, pero es una cifra **sin verificar**; mirar la consola entre ambas |

---

## 11. Calendario de preparación (5 días)

| Día | Qué |
|---|---|
| Dom 15 | Revisión de esta planificación (T00); empezar T01–T03 sin nube |
| Lun 16 | Scripts y pruebas sin GCP (T03–T07); borrador de teoría; T08 si hay cuenta; **T34 preparada antes de la noche (el devcontainer debe estar listo para la prueba del martes)**; T27 (pico técnico de la red neuronal, en local, sin gastar horas de Codespaces) |
| **Mar 17** | **[GCP] ensayo real con capturas (T08–T11) y, agrupada con él, la ÚNICA prueba larga del Codespace (T36)**; si T27 salió bien y hay tiempo, también T32 (ensayo de GKE, con T33 hecha antes); borrador de la guía |
| **Mié 18** | **S2.** Por la tarde [S2]: anotar incidencias, ajustar recap-02, fijar la lista de quién tiene proyecto e imagen |
| Jue 19 | Guía final con salidas reales, presentación, guion, rúbrica, índices, PDF, pruebas; ensayo cronometrado |
| Vie 20 (mañana) | Revisión final, proyecto y presupuesto listos, imagen empujada, capturas de respaldo abiertas, **sin restos de GKE** |

---

## 12. Decisiones del instructor del 15/11/2026 y sus consecuencias

Resumen: D1, D2, D3 y D5 quedan respondidas (marcadas con fecha en §10); D4 y D7 siguen abiertas. Tareas nuevas: **T27–T36** (en [`TAREAS-S3.md`](TAREAS-S3.md)); no se ha renumerado ninguna tarea existente. Horas: de ≈55 h a ≈79,5 h (+24,5 h, de ellas +5 h necesitan la cuenta real y +4,5 h son P1). Ver el detalle en el archivo de tareas.

### 12.1 D1 · Red neuronal como extra (T27–T31)
- **Qué es:** un ejemplo sencillo para demostrar que, igual que un modelo de ML, una red neuronal **se entrena, se registra en MLflow, se expone en Docker y se prueba en Codespaces**. Ejemplo preferido: clasificar imágenes de **perro/gato** con una red **ligera, que pese poco y corra en CPU**, **entrenada por nosotros** (o, si no es posible, ajustada a partir de otra). El instructor aún piensa el contenido exacto: **no se fija nada más** hasta tener el pico técnico.
- **Primero el pico técnico (T27)**, que decide con medidas: qué dataset y qué red caben en CPU y en una imagen Docker razonable; tiempos de entrenamiento medidos; cómo se registra en MLflow con firma y se carga con `mlflow-skinny`/`pyfunc`; tamaño de la imagen; alternativas si no se puede descargar el dataset o si `torch` pesa demasiado (p. ej. ONNX Runtime o una MLP de scikit-learn). **Sin cifras inventadas:** nada de pesos, tiempos ni exactitudes hasta medirlos.
- **Tareas del extra:** script de entrenamiento y registro (T28), API e imagen (T29), guía corta y 2–3 diapositivas (T30), pruebas (T31). Su prueba en Codespaces se agrupa con T36 (no hay una segunda).
- **Lugar en la sesión:** último extra o autoestudio (§3.1). **No está en el mínimo viable.**

### 12.2 D2 · Kubernetes con GKE (T32–T33)
- **Planteamiento:** con GCP, ya que habrá cuenta. La demo de GKE la hace **solo el instructor**, **documentada** (órdenes, salidas reales, tiempos). **TODO lo creado se ELIMINA al cerrar la práctica** (cluster, discos, balanceadores, IP; §8). El laboratorio **kind** se mantiene como autoestudio.
- **Tipo de cluster: sin verificar (Autopilot o Standard).** **Decisión pendiente**, que se toma con el ensayo (T32). Criterios: (1) **coste** (sin cifras aquí: se compara lo que muestre la consola de Facturación tras el ensayo; sin verificar); (2) **tiempo de creación** (se mide en el ensayo; sin verificar); (3) **facilidad y seguridad de la limpieza** (cuántos recursos sueltos deja: discos, balanceadores, IP; qué tan fácil es comprobar que no queda nada). Si el ensayo no se puede hacer, la demo se queda como material **sin verificar** y no se ejecuta en vivo.
- **Requisito antes de crear nada:** `limpiar.sh` y su comprobación posterior (listados vacíos y consola de Facturación al día siguiente) cubren GKE (T33).
- **No está en el mínimo viable.**

### 12.3 D3/D5 · Demo en Codespaces (T34–T36)
- **(a) Laboratorio preparado (T34):** `.devcontainer` con el SDK de Google Cloud: `gcloud`, `bq`, `gsutil`/`gcloud storage`, `kubectl` y el plugin de GKE si hace falta. **Qué forma de instalación es fiable en el devcontainer del curso (característica de devcontainer, instalación por apt o script) se verifica; no se da por supuesta ninguna:** no se escriben nombres de características sin comprobarlos. Se mide el tiempo extra de preparación y el peso.
- **(b) Guía para el alumno (T35):** instalar el SDK en VS Code de escritorio (Windows) y en el Codespace; autenticarse **sin pegar claves** (`gcloud auth login` con y sin navegador), `gcloud config`, proyecto y región por defecto, `gcloud auth list` y cómo cerrar sesión; conectar VS Code a GCP; con «qué debes ver» y «si falla».
- **(c) Prueba real (T36): UNA sola prueba larga**, agrupada con el ensayo del martes 17/11 (T08–T11). Hay **poca cuota de horas de Codespaces** (la cifra exacta, **sin verificar**), así que no se hacen pruebas sueltas: en esa misma sesión se prueba el devcontainer, la autenticación, el ensayo de la demo y, si están listas, la imagen de la red neuronal y las órdenes de GKE. Si algo falla se corrige dentro del mismo Codespace (script alternativo) y se anota; el ensayo cronometrado (T23) no abre otro Codespace.

### 12.4 Supuestos que siguen abiertos (D4, D7)
- **D7 (supuesto por defecto):** el alumno sin facturación sigue la **ruta sin nube con ensayo local** (scripts de migración y validación con destino local; lo demás documentado como «sin ejecutar»). Si el instructor responde otra cosa, se ajustan T13, T17 y la rúbrica.
- **D4 (región):** sin respuesta; se decide tras listar las ubicaciones reales en T08. Sigue sin afirmarse ninguna ventaja de precio.
