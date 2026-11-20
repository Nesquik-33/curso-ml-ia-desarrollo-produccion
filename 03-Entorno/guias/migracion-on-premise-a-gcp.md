# De on-premise a GCP: hilo de migración del curso

Estado: propuesta de diseño del 08/11/2026. Nada de esto está implementado ni probado.
Servicios, cuotas y precios de GCP cambian: verificarlos antes de impartir.

## Idea
En S1 y S2 todo corre «en local»: archivos, SQLite, scripts, MLflow y Docker en la máquina del alumno (o Codespace).
Eso hace de **on-premise simulado**: la situación de partida de muchos equipos. En S3 se migra a GCP, y en S4 y S5 se
automatiza y se opera. Así se enseña a extrapolar el caso a la nube y a migrar lo que ya existe.

## Mapa de equivalencias
| Componente del curso | Local / on-premise | GCP | Estrategia |
|---|---|---|---|
| Archivos originales (`data/raw`) | Carpeta o servidor de archivos | Cloud Storage (bucket, versionado de objetos) | Replatform |
| Capas `master_`, `fs_`, `ml_` | SQLite | BigQuery (analítico) o Cloud SQL (transaccional) | Replatform |
| Pipeline de datos y entrenamiento | Scripts manuales o `cron` | GitHub Actions (curso). Alternativas: Cloud Build, Cloud Scheduler + trabajos de Cloud Run, Vertex AI Pipelines, Cloud Composer | Refactor |
| Seguimiento y registro de modelos | MLflow con SQLite y carpeta local | MLflow con Cloud SQL y Cloud Storage. Alternativa: Vertex AI Experiments y Model Registry | Replatform |
| Imágenes | Docker local | Artifact Registry | Rehost |
| Servicio de la API | `uvicorn` en un servidor o máquina virtual | Cloud Run (alternativas: Compute Engine, GKE) | Rehost / Replatform |
| Credenciales | Archivo `.env` | Secret Manager | Replatform |
| Identidad y permisos | Usuarios y claves locales | IAM, cuentas de servicio con mínimos privilegios, Workload Identity Federation | Refactor |
| Registros, métricas y alertas | Archivos de log | Cloud Logging y Cloud Monitoring | Replatform |
| Tareas programadas | `cron` | Cloud Scheduler | Replatform |
| Costes | Hardware fijo | Presupuestos y alertas de facturación | Nuevo |

## Estrategias de migración (3 de las 6 «R»)
- **Rehost** (*lift and shift*): mover tal cual. Ejemplo: la imagen Docker del servicio pasa a Artifact Registry y Cloud Run.
- **Replatform:** mover cambiando la plataforma, con ajustes mínimos. Ejemplo: SQLite → BigQuery, archivos → Cloud Storage.
- **Refactor:** rediseñar para aprovechar la nube. Ejemplo: scripts manuales → workflow orquestado, claves → identidad federada.
Las otras (retener, retirar, recomprar) se mencionan, sin práctica.

## Fases de una migración
Evaluar (inventario y dependencias) → planificar (orden, riesgos, rollback) → ejecutar → optimizar (coste y operación).
Contrastar los nombres de las fases con la documentación vigente de Google Cloud antes de citarlos.

## Práctica propuesta en S3 (migrar el caso)
*Actualizado el 20/11/2026 con las correcciones del final (1, 2 y la del paso 6).* Pasos detallados: `01-Sesiones/S3-Despliegue-y-Redes-Neuronales/practica/guia-laboratorio.md`.
1. Inventario: listar qué usa el caso hoy (archivos, tablas, secretos, servicio, MLflow).
2. Exportar las tablas `master_`, `fs_` y `ml_` de SQLite a Parquet con `python -m ia_mlops.migracion exportar`, que escribe junto a los Parquet un `MANIFEST.sha256` (en `data/raw` no hay manifiesto; para otra carpeta se genera con `python -m ia_mlops.migracion huella generar CARPETA`). Subir la carpeta a Cloud Storage y comprobar la integridad **descargándola y recalculando el SHA-256** (`huella verificar`): Cloud Storage informa de MD5 y CRC32C, no de SHA-256 (sin verificar en la documentación vigente).
3. Cargar los Parquet en BigQuery.
4. **Validar la migración:** comparar conteos, esquemas y agregados entre SQLite y BigQuery. Estas comprobaciones se vuelven `pytest`.
5. Mover los secretos a Secret Manager y crear una cuenta de servicio con permisos mínimos.
6. Publicar la imagen en Artifact Registry y desplegarla en Cloud Run. La API **no lee datos ni secretos** (el modelo va dentro de la imagen): el servicio **no apunta a BigQuery**, que recibe una copia analítica validada; el secreto de la demo es un valor de ejemplo que el servicio no consume.
7. Documentar el plan de rollback (cómo volver a lo local si falla).

## Tarea
Migrar el caso propio a GCP y entregar el inventario, los resultados de validación, la configuración y los registros.

## Riesgos y cautelas
- **Costes:** usar presupuestos y alertas, borrar recursos al terminar y no crear nada de pago en S0. Verificar los límites gratuitos
  de BigQuery y Cloud Storage antes del curso.
- **Datos:** ningún dato sensible ni personal en la nube del curso. Comprobar la licencia antes de subir un dataset.
- **Carga de S3:** la sesión es densa (migración, despliegue y laboratorio de Kubernetes). El laboratorio de Kubernetes pasa a «si hay tiempo»
  y la parte neuronal sigue siendo opcional.
- **Acceso:** los alumnos necesitan proyecto de GCP con facturación habilitada o una alternativa (proyecto compartido del instructor).

## Pendiente
- Definir el proyecto de GCP por alumno o compartido, y el control de costes.
- Probar el flujo completo SQLite → Cloud Storage → BigQuery con el dataset elegido.
- Decidir si MLflow se migra a Cloud SQL y Cloud Storage en el curso o solo se menciona (Vertex AI como alternativa).
- Escribir los scripts de exportación, carga y validación.

## Correcciones propuestas tras T03 (15/11/2026)
Las correcciones 1 y 2 y la del paso 6 («apuntando a los datos») se aplicaron al texto de arriba el 20/11/2026; el resto de la guía (estado, riesgos, pendiente) sigue pendiente de T24.
1. **Paso 2 (`MANIFEST.sha256`).** En `04-Proyecto-Base/data/raw` no existe ese archivo (hay solo la muestra CSV). Propuesta: «genera el manifiesto con
   `python -m ia_mlops.migracion huella generar <carpeta>` antes de subir» y, para las tablas, `exportar` ya escribe `MANIFEST.sha256` junto a los Parquet
   (formato de `sha256sum`). Según la planificación, en el caso del alumnado la huella está en `02-Proyecto-Transversal/datos/SHA256SUMS` (no comprobado aquí).
2. **Paso 2 (comprobar la integridad «con el SHA-256»).** Cloud Storage informa de **MD5 y CRC32C** del objeto, no de SHA-256 (contrastar con la documentación vigente: sin verificar aquí).
   Propuesta: la huella SHA-256 se calcula en local antes de subir; la integridad en la nube se comprueba **descargando el objeto y recalculando su SHA-256**
   (`python -m ia_mlops.migracion huella verificar <carpeta descargada>`), o guardando la huella como metadato propio del objeto. No leyendo un SHA-256 del bucket.
3. **Paso 4 (validar).** Ya existe el código: `python -m ia_mlops.migracion validar --db ... --destino <carpeta de Parquet>` compara existencia, esquema (tipos lógicos),
   conteos, agregados y muestra, y sale con código ≠ 0 si algo difiere. Solo está probado **en local** (carpeta de Parquet); la fuente BigQuery está pendiente (T09).
4. **Parquet y `pyarrow`.** `pyarrow` no figuraba en los requirements del proyecto. El entorno del curso lo trae (`pyarrow=26.0.1` en `03-Entorno/conda/environment.yml`, versión
   comprobada con `import`); se añade `pyarrow==26.0.1` a `requirements-dev.txt` y el extra `migracion` a `pyproject.toml`. **No** se añade a `requirements-api.txt`: la imagen del servicio no lo usa.
   Sin `pyarrow`, `exportar` lo explica y las pruebas de migración se omiten.
5. **Sección «Pendiente».** «Escribir los scripts de exportación, carga y validación»: exportación y validación en local, hechas y probadas; carga a BigQuery y validación contra BigQuery, sin hacer.