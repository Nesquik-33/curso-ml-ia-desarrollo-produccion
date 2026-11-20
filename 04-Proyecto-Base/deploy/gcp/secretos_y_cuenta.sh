#!/usr/bin/env bash
# secretos_y_cuenta.sh - DEMO 2 (identidad): secreto de ejemplo y cuenta de servicio con UN solo permiso, sin claves.
#
# QUE CREA (solo con --ejecutar; por defecto SOLO MUESTRA las ordenes):
#   1. Un secreto de Secret Manager con etiqueta curso=ml-ia y UNA version con un valor de EJEMPLO, aleatorio y NO sensible
#      (no significa nada; no se imprime nunca). El servicio actual de la API NO lo consume: es para aprender el mecanismo.
#   2. Una cuenta de servicio (sa-retencion-api por defecto) SIN claves JSON; su descripcion lleva curso=ml-ia (las cuentas no tienen etiquetas).
#   3. UN permiso: roles/secretmanager.secretAccessor concedido sobre ESE secreto (no sobre el proyecto). Sin roles de Storage ni de BigQuery:
#      lo que la API no usa no se concede.
# QUE CUESTA: puede generar coste (versiones de secreto, accesos); ver el presupuesto. La cuenta de servicio no cuesta por si misma.
# COMO SE BORRA: ./limpiar.sh --confirmar (cuenta de servicio y secreto con su politica). Comprobacion: listados al final de limpiar.sh.
# Comprobaciones que hace al final: la politica del secreto y que la cuenta NO aparece en las politicas del proyecto (debe salir vacio).
# Sin verificar contra GCP real: opciones y nombre del rol (T10).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/_comun.sh"
iniciar "$@"
necesita_herramienta gcloud

valor_de_ejemplo() {      # aleatorio, sin significado y sin datos reales; en modo mostrar ni se genera
  if [ "$REAL" = "si" ]; then od -An -N16 -tx1 /dev/urandom | tr -d ' \n'; else printf 'valor-aleatorio-de-ejemplo'; fi
}

paso "1. Secreto de ejemplo (valor aleatorio no sensible; nunca se imprime)"
correr gcloud secrets create "$SECRETO" --project "$PROYECTO" --replication-policy=user-managed --locations="$REGION" --labels=curso=ml-ia
valor_de_ejemplo | correr_stdin gcloud secrets versions add "$SECRETO" --project "$PROYECTO" --data-file=-

paso "2. Cuenta de servicio SIN claves"
correr gcloud iam service-accounts create "$CUENTA_SERVICIO" --project "$PROYECTO" --display-name "Demo curso ML" --description "curso=ml-ia: identidad de ejecucion de la API de la demo"

paso "3. Un solo permiso: leer ESE secreto"
correr gcloud secrets add-iam-policy-binding "$SECRETO" --project "$PROYECTO" --member "serviceAccount:$CUENTA_SERVICIO_EMAIL" --role roles/secretmanager.secretAccessor

paso "Comprobaciones (solo lecturas)"
leer gcloud secrets get-iam-policy "$SECRETO" --project "$PROYECTO"
leer gcloud secrets versions list "$SECRETO" --project "$PROYECTO"
leer gcloud iam service-accounts keys list --iam-account "$CUENTA_SERVICIO_EMAIL" --managed-by=user
nota "la lista de claves de usuario debe salir VACIA: la cuenta no tiene claves JSON"
echo "+ gcloud projects get-iam-policy $PROYECTO --flatten=bindings[].members --filter=bindings.members:$CUENTA_SERVICIO --format='value(bindings.role)'    (debe salir VACIO)"
if [ "$REAL" = "si" ] || [ "$SOLO_COMPROBAR" = "si" ]; then
  gcloud projects get-iam-policy "$PROYECTO" --flatten='bindings[].members' --filter="bindings.members:$CUENTA_SERVICIO" --format='value(bindings.role)'
fi