#!/usr/bin/env bash
# preparar_proyecto.sh - comprobacion previa, APIs necesarias y presupuesto con alerta.
#
# QUE HACE (por defecto SOLO MUESTRA las ordenes; --comprobar ejecuta solo las lecturas; --ejecutar habilita APIs y crea el presupuesto):
#   1. Comprobacion previa (lecturas): gcloud instalado, cuenta activa (no se imprime el correo), proyecto, facturacion habilitada.
#   2. Habilita SOLO las APIs necesarias (Storage, BigQuery, Artifact Registry, Cloud Run, Secret Manager, IAM, Facturacion/Presupuestos).
#   3. Crea un presupuesto con alertas por umbrales ANTES que cualquier recurso (si faltan la cuenta de facturacion y el importe, no se crea).
# QUE CUESTA: habilitar APIs no crea recursos; los presupuestos y las alertas no cuestan. Una alerta AVISA, no corta el gasto (a comprobar
#   en la documentacion vigente). Todo lo demas puede generar coste; ver el presupuesto.
# COMO SE BORRA: las APIs se pueden dejar habilitadas (no cobran por estarlo). El presupuesto: ./limpiar.sh --confirmar --incluir-presupuesto
#   o en la consola de Facturacion. Si tu cuenta no permite crearlo por CLI, hazlo a mano: Facturacion > Presupuestos y alertas > Crear.
# Variables: CURSO_GCP_PROYECTO, CURSO_GCP_REGION, CURSO_GCP_CUENTA_FACTURACION, CURSO_GCP_PRESUPUESTO_IMPORTE (ver env.ejemplo.sh).
# Sin verificar contra GCP real: nombres de opciones y de APIs (se contrastan con --help en T08).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/_comun.sh"
iniciar "$@"

APIS="storage.googleapis.com bigquery.googleapis.com artifactregistry.googleapis.com run.googleapis.com secretmanager.googleapis.com iam.googleapis.com cloudbilling.googleapis.com billingbudgets.googleapis.com"
# GKE (T32): container.googleapis.com y compute.googleapis.com se habilitarian aqui SOLO para la demo del instructor; no estan en el camino del alumno.

comprobar_previa() {
  paso "1. Comprobacion previa (solo lecturas)"
  necesita_herramienta gcloud
  leer gcloud version
  echo "+ gcloud auth list --filter=status:ACTIVE --format='value(account)'    (se cuenta; el correo NO se imprime)"
  if [ "$REAL" = "si" ] || [ "$SOLO_COMPROBAR" = "si" ]; then
    n="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | grep -c .)"
    if [ "$n" -ge 1 ]; then echo "OK: hay una cuenta activa."; else echo "NO hay cuenta activa: ejecuta 'gcloud auth login' (con --no-browser en el Codespace). No pegues claves." >&2; exit 1; fi
  fi
  leer gcloud projects describe "$PROYECTO" --format='value(projectId,lifecycleState)'
  echo "+ gcloud billing projects describe $PROYECTO --format='value(billingEnabled)'    (debe decir True)"
  if [ "$REAL" = "si" ] || [ "$SOLO_COMPROBAR" = "si" ]; then
    if [ "$(gcloud billing projects describe "$PROYECTO" --format='value(billingEnabled)')" = "True" ]; then echo "OK: facturacion habilitada."
    else echo "La facturacion NO esta habilitada en el proyecto: sin ella no se pueden crear los recursos (ruta sin nube: ver la guia)." >&2; exit 1; fi
  fi
  leer gcloud services list --enabled --project "$PROYECTO" --format='value(config.name)'
}

comprobar_previa

paso "2. Habilitar las APIs necesarias (--ejecutar)"
if [ "$SOLO_COMPROBAR" = "si" ] && [ "$REAL" != "si" ]; then nota "omitido en --comprobar"; else
  # shellcheck disable=SC2086
  correr gcloud services enable $APIS --project "$PROYECTO"
fi

paso "3. Presupuesto y alerta, ANTES de crear ningun recurso (--ejecutar)"
if [ "$SOLO_COMPROBAR" = "si" ] && [ "$REAL" != "si" ]; then nota "omitido en --comprobar"; else
  requerir CURSO_GCP_CUENTA_FACTURACION "ID de la cuenta de facturacion: gcloud billing accounts list"
  requerir CURSO_GCP_PRESUPUESTO_IMPORTE "importe del presupuesto, elegido por ti"
  correr gcloud billing budgets create --billing-account "$CUENTA_FACTURACION" --display-name "$PRESUPUESTO_NOMBRE" \
    --budget-amount "$PRESUPUESTO_IMPORTE" --filter-projects "projects/$PROYECTO" \
    --threshold-rule percent=0.5 --threshold-rule percent=0.9 --threshold-rule percent=1.0
  nota "un presupuesto avisa, NO corta el gasto: comprobarlo en la documentacion vigente; los presupuestos no admiten la etiqueta curso=ml-ia (se localiza por el nombre $PRESUPUESTO_NOMBRE)"
fi

paso "Comprobacion posterior"
leer gcloud billing budgets list --billing-account "$CUENTA_FACTURACION"