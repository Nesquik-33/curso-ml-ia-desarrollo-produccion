#!/usr/bin/env bash
# desplegar.sh - DEMO 2 (servicio): Cloud Run PRIVADO con la imagen de etiqueta fija, la cuenta de servicio minima y el secreto.
#
# QUE CREA (solo con --ejecutar; por defecto SOLO MUESTRA las ordenes):
#   Un servicio de Cloud Run (etiqueta curso=ml-ia) con: --no-allow-unauthenticated (privado; nada de allUsers), instancias minimas 0,
#   instancias maximas bajas (CURSO_GCP_MAX_INSTANCIAS, 2 por defecto), la cuenta de servicio sa-retencion-api, el secreto montado
#   como variable de entorno (version fija 1, no "latest"), puerto 8080 y CURSO_LOG_NIVEL=INFO. La memoria solo se fija si
#   CURSO_GCP_MEMORIA tiene valor: se MIDE antes con `docker stats`, no se adivina.
#   Nunca se despliega por la etiqueta "latest": la imagen es la de CURSO_GCP_ETIQUETA_IMAGEN (la que subio imagen.sh).
# QUE CUESTA: puede generar coste (instancias de Cloud Run mientras atienden peticiones); ver el presupuesto. Con minimas 0 no hay instancia en reposo.
# COMO SE BORRA: ../gcp/limpiar.sh --confirmar (servicio primero). Comprobacion: listados al final de limpiar.sh.
# Requisitos: haber ejecutado preparar_proyecto.sh, secretos_y_cuenta.sh e imagen.sh.
# Sin verificar contra GCP real: opciones de gcloud run deploy (T10).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/../gcp/_comun.sh"
iniciar "$@"
necesita_herramienta gcloud

OPCIONES_EXTRA=()
[ -n "$MEMORIA" ] && OPCIONES_EXTRA+=(--memory "$MEMORIA")

paso "Desplegar $SERVICIO (privado, minimo 0, maximo $MAX_INSTANCIAS) con la imagen $IMAGEN:$ETIQUETA_IMAGEN"
[ -z "$MEMORIA" ] && nota "memoria sin fijar: mide primero con docker stats y define CURSO_GCP_MEMORIA"
correr gcloud run deploy "$SERVICIO" --project "$PROYECTO" --region "$REGION" --image "$IMAGEN_COMPLETA" \
  --no-allow-unauthenticated --min-instances 0 --max-instances "$MAX_INSTANCIAS" --port 8080 \
  --service-account "$CUENTA_SERVICIO_EMAIL" --set-secrets "CURSO_DEMO_SECRETO=$SECRETO:1" \
  --set-env-vars CURSO_LOG_NIVEL=INFO --labels=curso=ml-ia "${OPCIONES_EXTRA[@]}"

paso "Comprobacion (solo lecturas): el servicio NO debe permitir invocaciones publicas"
leer gcloud run services describe "$SERVICIO" --project "$PROYECTO" --region "$REGION" --format 'value(status.url,spec.template.spec.serviceAccountName)'
leer gcloud run services get-iam-policy "$SERVICIO" --project "$PROYECTO" --region "$REGION"