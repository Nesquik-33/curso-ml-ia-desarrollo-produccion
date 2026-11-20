#!/usr/bin/env bash
# datos.sh - DEMO 1 (datos): bucket, Parquet con huella, dataset y carga en BigQuery, y validacion contra BigQuery.
#
# QUE CREA (solo con --ejecutar; por defecto SOLO MUESTRA las ordenes):
#   1. Un bucket de Cloud Storage: region unica, acceso uniforme a nivel de bucket, prevencion de acceso publico, etiqueta curso=ml-ia.
#   2. Los Parquet de `python -m ia_mlops.migracion exportar` (con esquema.json, conteos.json y MANIFEST.sha256) en una carpeta
#      temporal local y su subida al bucket; se descarga y se verifica la huella SHA-256 (Cloud Storage no da SHA-256, solo MD5/CRC32C).
#   3. Un dataset de BigQuery en la MISMA ubicacion que el bucket, con caducidad por defecto de las tablas y etiqueta curso=ml-ia.
#   4. Una tabla por cada Parquet (`bq load --source_format=PARQUET`), con la etiqueta curso:ml-ia.
#   5. La validacion `python -m ia_mlops.migracion validar --bigquery ...` (FuenteBigQuery: dry run y tope de bytes facturados).
# QUE CUESTA: puede generar coste (almacenamiento en el bucket y en BigQuery, consultas); ver el presupuesto. Las consultas llevan dry run y tope.
# COMO SE BORRA: ./limpiar.sh --confirmar (dataset con sus tablas y bucket vaciado). Comprobacion: los listados del final de limpiar.sh.
# Requisitos (en modo real): gcloud, bq, el Python del curso con pyarrow y la biblioteca google-cloud-bigquery para el paso 5
#   (NO se instala nada desde estos scripts), y haber ejecutado preparar_proyecto.sh.
# Variables: CURSO_GCP_PROYECTO, CURSO_GCP_REGION, CURSO_GCP_PREFIJO, CURSO_GCP_DB, CURSO_GCP_TRABAJO, CURSO_GCP_TABLAS (ver env.ejemplo.sh).
# Sin verificar contra GCP real: opciones de gcloud/bq, tipos resultantes en BigQuery y tiempos (T09).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/_comun.sh"
iniciar "$@"
cd "$DIR_PROYECTO" || exit 2
necesita_herramienta gcloud
necesita_herramienta bq
DESCARGA="${TRABAJO}-descarga"

paso "0. Inventario y comprobacion previa (solo lecturas, locales)"
leer "$PYTHON" -m ia_mlops.migracion inventario --db "$BASE_SQLITE"

paso "1. Bucket: region unica, acceso uniforme, sin acceso publico, etiqueta curso=ml-ia"
correr gcloud storage buckets create "gs://$BUCKET" --project "$PROYECTO" --location "$REGION" --uniform-bucket-level-access --public-access-prevention
correr gcloud storage buckets update "gs://$BUCKET" --update-labels=curso=ml-ia

paso "2. Exportar a Parquet (con MANIFEST.sha256), subir y verificar la huella"
correr "$PYTHON" -m ia_mlops.migracion exportar --db "$BASE_SQLITE" --salida "$TRABAJO"
correr gcloud storage rsync "$TRABAJO" "gs://$BUCKET/parquet"
correr gcloud storage rsync "gs://$BUCKET/parquet" "$DESCARGA"
correr "$PYTHON" -m ia_mlops.migracion huella verificar "$DESCARGA"

paso "3. Dataset de BigQuery (misma ubicacion que el bucket, tablas con caducidad, etiqueta curso:ml-ia)"
correr bq --project_id "$PROYECTO" --location "$REGION" mk --dataset --default_table_expiration "$CADUCIDAD_TABLAS_SEG" --label curso:ml-ia \
  --description "Demo del curso: copia analitica validada" "$PROYECTO:$DATASET"

paso "4. Cargar cada Parquet en su tabla"
for t in $TABLAS; do
  correr bq --project_id "$PROYECTO" --location "$REGION" load --source_format=PARQUET --replace "$PROYECTO:$DATASET.$t" "gs://$BUCKET/parquet/$t.parquet"
  correr bq --project_id "$PROYECTO" update --set_label curso:ml-ia "$PROYECTO:$DATASET.$t"
done

paso "5. Validar contra BigQuery (dry run + tope de bytes en cada consulta; sale con codigo distinto de 0 si algo difiere)"
if [ "$REAL" = "si" ] && ! "$PYTHON" -c "import google.cloud.bigquery" > /dev/null 2>&1; then
  echo "Falta la biblioteca google-cloud-bigquery en el Python del curso. Instalala en TU entorno (no la instalan estos scripts) y repite solo este paso." >&2
  exit 3
fi
correr "$PYTHON" -m ia_mlops.migracion validar --db "$BASE_SQLITE" --bigquery "$PROYECTO.$DATASET" --ubicacion "$REGION" --max-bytes "$MAX_BYTES" --json "$TRABAJO/validacion-bigquery.json"

paso "Listados de comprobacion"
leer gcloud storage ls "gs://$BUCKET/parquet/"
leer bq --project_id "$PROYECTO" --location "$REGION" ls "$PROYECTO:$DATASET"