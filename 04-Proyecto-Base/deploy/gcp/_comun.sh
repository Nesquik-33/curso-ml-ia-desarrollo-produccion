#!/usr/bin/env bash
# _comun.sh - funciones y nombres compartidos por los scripts de deploy/gcp y deploy/cloud-run. Se carga con `source`; no se ejecuta.
#
# QUE CREA:  nada (solo define funciones y calcula nombres a partir de las variables CURSO_GCP_*).
# QUE CUESTA: nada por si mismo.
# COMO SE BORRA: no hay nada que borrar.
#
# Reglas que cumplen TODOS los scripts (las vigila tests/test_scripts_gcp.py):
#   * Por defecto SOLO MUESTRAN las ordenes que ejecutarian (modo "mostrar"); no hace falta gcloud, bq ni docker instalados.
#   * Crear recursos exige --ejecutar. Borrar exige --confirmar (solo limpiar.sh).
#   * Todo lo que se crea lleva la etiqueta curso=ml-ia (o curso:ml-ia en bq) donde el servicio la admite.
#   * Ninguna ID de proyecto, correo, clave ni region reales viven en el repositorio: todo sale de variables de entorno CURSO_GCP_*
#     (copia env.ejemplo.sh a env.sh, que esta en .gitignore).
#   * Nada publico (sin allUsers) y nada desplegado por la etiqueta "latest".
# SIN VERIFICAR contra GCP real: las opciones de gcloud/bq se contrastan con `--help` en T08-T10.

set -u

DIR_GCP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR_PROYECTO="$(cd "$DIR_GCP/../.." && pwd)"

ETIQUETA_GCP="curso=ml-ia"       # gcloud: clave=valor
ETIQUETA_BQ="curso:ml-ia"        # bq: clave:valor

MODO="mostrar"           # mostrar | ejecutar
CONFIRMADO="no"          # solo limpiar.sh
SOLO_COMPROBAR="no"      # lecturas (no crea nada) en preparar_proyecto.sh
REAL="no"                # "si" cuando las ordenes se ejecutan de verdad
SCRIPT_BORRA="no"        # limpiar.sh lo pone a "si": su interruptor es --confirmar y no --ejecutar
AYUDA_TEXTO=""

# ---------------------------------------------------------------------------------------------------------- argumentos
iniciar() {
  local a
  for a in "$@"; do
    case "$a" in
      --ejecutar)  MODO="ejecutar" ;;
      --confirmar) CONFIRMADO="si" ;;
      --comprobar) SOLO_COMPROBAR="si" ;;
      -h|--help|--ayuda) mostrar_ayuda; exit 0 ;;
      *) echo "Opcion desconocida: $a (usa --ayuda)" >&2; exit 2 ;;
    esac
  done
  if [ "$SCRIPT_BORRA" = "si" ]; then
    if [ "$MODO" = "ejecutar" ]; then echo "limpiar.sh borra con --confirmar (no con --ejecutar)." >&2; exit 2; fi
    [ "$CONFIRMADO" = "si" ] && REAL="si"
  else
    if [ "$CONFIRMADO" = "si" ]; then echo "--confirmar es solo de limpiar.sh; aqui se crea con --ejecutar." >&2; exit 2; fi
    [ "$MODO" = "ejecutar" ] && REAL="si"
  fi
  [ -f "$DIR_GCP/env.sh" ] && . "$DIR_GCP/env.sh"
  calcular_nombres
  if [ "$REAL" = "si" ] || [ "$SOLO_COMPROBAR" = "si" ]; then comprobar_variables; fi
  cabecera_modo
}

mostrar_ayuda() {
  # imprime el bloque de comentarios del script que llama (desde la 2.a linea hasta la primera linea que no es comentario)
  sed -n '2,/^[^#]/p' "$0" | sed -n '/^#/s/^# \{0,1\}//p'
  echo
  echo "Opciones: sin nada = MOSTRAR lo que haria; --ejecutar = crear de verdad; --confirmar (solo limpiar.sh) = borrar de verdad; --comprobar (solo lecturas)."
}

cabecera_modo() {
  if [ "$REAL" = "si" ]; then
    echo "### MODO REAL: las ordenes de abajo SE EJECUTAN contra GCP (proyecto $PROYECTO)."
  elif [ "$SOLO_COMPROBAR" = "si" ]; then
    echo "### MODO COMPROBAR: solo lecturas (no crea ni borra nada)."
  else
    echo "### MODO MOSTRAR: solo se imprimen las ordenes, NO se ejecuta nada. Para ejecutarlas anade $([ "$SCRIPT_BORRA" = "si" ] && echo --confirmar || echo --ejecutar)."
  fi
}

# ---------------------------------------------------------------------------------------------------------- nombres
calcular_nombres() {
  # Marcadores (sin caracteres especiales) para poder IMPRIMIR las ordenes sin configurar nada; en modo real se exigen valores reales.
  PROYECTO="${CURSO_GCP_PROYECTO:-TU-PROYECTO}"
  REGION="${CURSO_GCP_REGION:-TU-REGION}"
  PREFIJO="${CURSO_GCP_PREFIJO:-curso-ml}"
  CUENTA_FACTURACION="${CURSO_GCP_CUENTA_FACTURACION:-TU-CUENTA-DE-FACTURACION}"
  PRESUPUESTO_IMPORTE="${CURSO_GCP_PRESUPUESTO_IMPORTE:-TU-IMPORTE}"
  ETIQUETA_IMAGEN="${CURSO_GCP_ETIQUETA_IMAGEN:-s3-1}"
  PYTHON="${CURSO_GCP_PYTHON:-python}"
  TRABAJO="${CURSO_GCP_TRABAJO:-/tmp/curso-gcp-parquet}"
  PUERTO_PROXY="${CURSO_GCP_PUERTO_PROXY:-8081}"
  CADUCIDAD_TABLAS_SEG="${CURSO_GCP_CADUCIDAD_TABLAS_SEG:-604800}"    # decision nuestra (7 dias), no una cifra de Google
  MAX_BYTES="${CURSO_GCP_MAX_BYTES:-1000000000}"                      # tope de bytes facturados por consulta (decision nuestra)
  MAX_INSTANCIAS="${CURSO_GCP_MAX_INSTANCIAS:-2}"
  MEMORIA="${CURSO_GCP_MEMORIA:-}"                                     # sin valor por defecto: se mide con docker stats
  TABLAS="${CURSO_GCP_TABLAS:-master_calidad master_clientes master_descartes master_facturas master_lineas master_productos fs_catalogo fs_cliente_corte ml_dataset ml_particiones}"
  BASE_SQLITE="${CURSO_GCP_DB:-data/processed/curso.db}"

  BUCKET="${CURSO_GCP_BUCKET:-${PROYECTO}-${PREFIJO}-datos}"
  DATASET="${CURSO_GCP_DATASET:-${PREFIJO//-/_}}"                      # BigQuery admite guion bajo, no guion
  REPO_AR="${CURSO_GCP_REPO_AR:-${PREFIJO}-imagenes}"
  IMAGEN="${CURSO_GCP_IMAGEN:-retencion-api}"
  SERVICIO="${CURSO_GCP_SERVICIO:-retencion-api}"
  CUENTA_SERVICIO="${CURSO_GCP_CUENTA_SERVICIO:-sa-retencion-api}"
  CUENTA_SERVICIO_EMAIL="${CUENTA_SERVICIO}@${PROYECTO}.iam.gserviceaccount.com"
  SECRETO="${CURSO_GCP_SECRETO:-${PREFIJO}-demo-secreto}"
  CLUSTER_GKE="${CURSO_GCP_GKE_CLUSTER:-${PREFIJO}-gke}"
  PRESUPUESTO_NOMBRE="${PREFIJO}-presupuesto"
  IMAGEN_COMPLETA="${REGION}-docker.pkg.dev/${PROYECTO}/${REPO_AR}/${IMAGEN}:${ETIQUETA_IMAGEN}"
}

comprobar_variables() {
  local faltan=() v
  for v in CURSO_GCP_PROYECTO CURSO_GCP_REGION; do
    [ -n "${!v:-}" ] || faltan+=("$v")
  done
  if [ "${#faltan[@]}" -gt 0 ]; then
    echo "Faltan variables de entorno: ${faltan[*]} (copia env.ejemplo.sh a env.sh y rellenala)." >&2
    exit 2
  fi
  case "$ETIQUETA_IMAGEN" in
    latest|"") echo "La etiqueta de la imagen no puede ser latest ni estar vacia: usa una etiqueta fija (CURSO_GCP_ETIQUETA_IMAGEN)." >&2; exit 2 ;;
  esac
}

requerir() {      # requerir VARIABLE "para que sirve": solo se exige en modo real
  if [ "$REAL" = "si" ] && [ -z "${!1:-}" ]; then echo "Falta $1 ($2)." >&2; exit 2; fi
}

# ---------------------------------------------------------------------------------------------------------- ejecutar o mostrar
# correr ORDEN...   imprime la orden; solo la ejecuta en modo real. Si falla, se para.
correr() {
  printf '+'; printf ' %q' "$@"; printf '\n'
  [ "$REAL" = "si" ] || return 0
  "$@" || { echo "ERROR: ha fallado la orden anterior; se para aqui." >&2; exit 1; }
}

# correr_stdin ORDEN...   igual, para una orden que lee la entrada estandar (una tuberia): en modo mostrar la vacia sin leerla.
correr_stdin() {
  printf '+ (entrada por tuberia) |'; printf ' %q' "$@"; printf '\n'
  if [ "$REAL" != "si" ]; then cat > /dev/null; return 0; fi
  "$@" || { echo "ERROR: ha fallado la orden anterior; se para aqui." >&2; exit 1; }
}

# leer ORDEN...   una LECTURA (listados, comprobaciones): se imprime siempre y se ejecuta en modo real o --comprobar. No crea nada.
leer() {
  printf '+'; printf ' %q' "$@"; printf '\n'
  [ "$REAL" = "si" ] || [ "$SOLO_COMPROBAR" = "si" ] || return 0
  "$@" || echo "(la lectura anterior ha fallado o no ha devuelto nada)" >&2
  return 0
}

# borrar ORDEN...   un BORRADO: tolerante (si el recurso ya no existe, sigue). Solo se ejecuta con --confirmar.
borrar() {
  printf '+'; printf ' %q' "$@"; printf '\n'
  [ "$REAL" = "si" ] || return 0
  "$@" || echo "(no se pudo borrar o ya no existia; se continua)" >&2
  return 0
}

paso() { echo; echo "== $*"; }
nota() { echo "   ($*)"; }

# necesita_herramienta HERRAMIENTA   en modo real, falla si no esta instalada; en modo mostrar no hace falta.
necesita_herramienta() {
  if [ "$REAL" = "si" ] || [ "$SOLO_COMPROBAR" = "si" ]; then
    command -v "$1" > /dev/null 2>&1 || { echo "Falta '$1' en el PATH (en el Codespace del curso viene instalado)." >&2; exit 2; }
  fi
}
