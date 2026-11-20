#!/usr/bin/env bash
# probar.sh - DEMO 2 (prueba): `gcloud run services proxy` + el script de comparacion de S2 + lectura de registros.
#
# QUE CREA: nada en GCP. Abre un proxy LOCAL (con tu identidad, sin tocar el codigo de la API ni exponerla) en un puerto de tu maquina
#   y lo cierra al terminar. Por defecto SOLO MUESTRA las ordenes; con --ejecutar las ejecuta.
# QUE HACE: /salud, /listo, /modelo, una prediccion con tests/datos/cliente_ejemplo.json, `python -m ia_mlops.modeling.comparar --url ...`
#   y despues lee los registros del servicio (para seguir un X-Request-ID y comprobar que ninguna linea lleva datos del cliente).
# QUE CUESTA: puede generar coste (peticiones al servicio; lectura de registros); ver el presupuesto.
# COMO SE BORRA: nada que borrar (el proxy se cierra solo; ../gcp/limpiar.sh borra el servicio).
# Variables: CURSO_GCP_PUERTO_PROXY (8081 por defecto: evita el 8080 si esta ocupado).
# Sin verificar contra GCP real: gcloud run services proxy y comparar sobre el servicio (T10).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/../gcp/_comun.sh"
iniciar "$@"
cd "$DIR_PROYECTO" || exit 2
necesita_herramienta gcloud
URL="http://127.0.0.1:$PUERTO_PROXY"
ID_PETICION="prueba-s3-$(date +%s)"

paso "1. Proxy local hacia el servicio privado (segundo plano)"
echo "+ gcloud run services proxy $SERVICIO --project $PROYECTO --region $REGION --port $PUERTO_PROXY &"
if [ "$REAL" = "si" ]; then
  gcloud run services proxy "$SERVICIO" --project "$PROYECTO" --region "$REGION" --port "$PUERTO_PROXY" &
  PID_PROXY=$!
  trap 'kill "$PID_PROXY" 2> /dev/null' EXIT
  sleep 5
fi

paso "2. Vivo, listo, modelo y una prediccion"
correr curl -fsS "$URL/salud"
correr curl -fsS "$URL/listo"
correr curl -fsS "$URL/modelo"
correr curl -fsS -X POST "$URL/predecir" -H "Content-Type: application/json" -H "X-Request-ID: $ID_PETICION" -d @tests/datos/cliente_ejemplo.json

paso "3. Comparacion de S2 contra el servicio (diferencias cero, o explicadas)"
correr "$PYTHON" -m ia_mlops.modeling.comparar --url "$URL"

paso "4. Registros (busca $ID_PETICION; ninguna linea debe llevar datos del cliente)"
leer gcloud run services logs read "$SERVICIO" --project "$PROYECTO" --region "$REGION" --limit 50
leer gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICIO" --project "$PROYECTO" --limit 20 --format json