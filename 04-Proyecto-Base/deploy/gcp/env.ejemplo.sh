#!/usr/bin/env bash
# env.ejemplo.sh - variables de los scripts de deploy/gcp y deploy/cloud-run. NO contiene ningun valor real.
#
# Como se usa:  cp env.ejemplo.sh env.sh   y rellena env.sh con TUS valores.
#               env.sh esta en .gitignore: NO lo subas nunca (ni pegues en el repositorio un ID de proyecto, un correo o una clave).
# QUE CREA:  nada.   QUE CUESTA: nada.   COMO SE BORRA: borra tu env.sh si ya no lo quieres.
#
# Si no rellenas nada, los scripts siguen funcionando en modo "mostrar" (imprimen las ordenes con marcadores TU-...).

# --- obligatorias para ejecutar de verdad (--ejecutar / --confirmar)
export CURSO_GCP_PROYECTO=""            # el ID de TU proyecto desechable (lo da GCP al crearlo)
export CURSO_GCP_REGION=""              # UNA sola region para todo; se elige tras listar las ubicaciones reales (decision D4, sin verificar)

# --- presupuesto (preparar_proyecto.sh): se crea ANTES que cualquier recurso
export CURSO_GCP_CUENTA_FACTURACION=""  # ID de tu cuenta de facturacion (gcloud billing accounts list)
export CURSO_GCP_PRESUPUESTO_IMPORTE="" # importe pequeno que TU eliges, con su moneda (formato del --help de gcloud billing budgets create)

# --- opcionales (hay valores por defecto)
# export CURSO_GCP_PREFIJO="curso-ml"            # prefijo de los nombres de todo lo que se crea
# export CURSO_GCP_ETIQUETA_IMAGEN="s3-1"        # etiqueta FIJA de la imagen (nunca latest)
# export CURSO_GCP_PYTHON="python"               # el Python del entorno del curso (el que tiene pyarrow)
# export CURSO_GCP_DB="data/processed/curso.db"  # SQLite de origen (relativa a 04-Proyecto-Base)
# export CURSO_GCP_TRABAJO="/tmp/curso-gcp-parquet"   # carpeta temporal de los Parquet
# export CURSO_GCP_MAX_INSTANCIAS="2"            # maximo de instancias de Cloud Run (bajo)
# export CURSO_GCP_MEMORIA=""                    # memoria de Cloud Run: se MIDE antes con docker stats; vacia = no se fija
# export CURSO_GCP_PUERTO_PROXY="8081"           # puerto local del proxy (evita el 8080 si esta ocupado)
# export CURSO_GCP_CADUCIDAD_TABLAS_SEG="604800" # caducidad por defecto de las tablas de BigQuery (decision nuestra)
# export CURSO_GCP_MAX_BYTES="1000000000"        # tope de bytes facturados por consulta de validacion (decision nuestra)