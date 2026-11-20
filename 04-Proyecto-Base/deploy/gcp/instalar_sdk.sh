#!/usr/bin/env bash
# Instala el SDK de Google Cloud (gcloud, bq, gcloud storage) y el complemento de autenticacion de GKE en un Codespace
# (Debian/Ubuntu). Se ejecuta BAJO DEMANDA: el arranque por defecto del Codespace no lo llama.
#   bash 04-Proyecto-Base/deploy/gcp/instalar_sdk.sh              instala lo que falte y verifica versiones
#   bash 04-Proyecto-Base/deploy/gcp/instalar_sdk.sh --comprobar  no instala nada: dice que hay y que faltaria
# Metodo: repositorio apt de Google Cloud con su clave, segun https://docs.cloud.google.com/sdk/docs/install (leida el 15/11/2026).
# SIN VERIFICAR EN UN CODESPACE REAL: se prueba en T36. No usa claves ni cuentas: la autenticacion es aparte (gcloud auth login).
set -euo pipefail

MODO="instalar"
case "${1:-}" in
  "") ;;
  --comprobar) MODO="comprobar" ;;
  -h|--help|--ayuda) sed -n '2,7p' "$0"; exit 0 ;;
  *) echo "Opcion desconocida: $1 (usa --comprobar o --ayuda)" >&2; exit 2 ;;
esac

CLAVE=/usr/share/keyrings/cloud.google.gpg
LISTA=/etc/apt/sources.list.d/google-cloud-sdk.list
URL_CLAVE="https://packages.cloud.google.com/apt/doc/apt-key.gpg"
LINEA_APT="deb [signed-by=${CLAVE}] https://packages.cloud.google.com/apt cloud-sdk main"

tiene() { command -v "$1" >/dev/null 2>&1; }

faltan=()
tiene gcloud || faltan+=("google-cloud-cli")
tiene gke-gcloud-auth-plugin || faltan+=("google-cloud-cli-gke-gcloud-auth-plugin")
tiene kubectl || faltan+=("kubectl")   # normalmente ya lo trae el devcontainer del curso

mostrar_versiones() {
  local fallos=0
  verif() { # nombre, comando...
    local n="$1"; shift
    if salida="$("$@" 2>&1)"; then printf '[OK   ] %-24s %s\n' "$n" "$(echo "$salida" | head -1)"
    else printf '[FALTA] %-24s %s\n' "$n" "$(echo "$salida" | head -1)"; fallos=$((fallos+1)); fi
  }
  verif "gcloud version"        gcloud version
  verif "bq version"            bq version
  verif "gcloud storage"        bash -c 'gcloud storage --help | head -1'
  verif "kubectl (cliente)"     kubectl version --client
  verif "gke-gcloud-auth-plugin" gke-gcloud-auth-plugin --version
  return "$fallos"
}

if [ "$MODO" = "comprobar" ]; then
  if [ "${#faltan[@]}" -eq 0 ]; then echo "Nada que instalar: todo esta presente."
  else echo "Faltaria instalar (paquetes apt): ${faltan[*]}"; fi
  mostrar_versiones || true
  exit 0
fi

if [ "${#faltan[@]}" -eq 0 ]; then
  echo "Ya esta todo instalado; solo se verifica."
else
  sudo apt-get update
  sudo apt-get install -y ca-certificates gnupg curl
  if [ ! -s "$CLAVE" ]; then
    curl -fsSL "$URL_CLAVE" | sudo gpg --dearmor -o "$CLAVE"
  fi
  if ! grep -qsF "$LINEA_APT" "$LISTA"; then
    echo "$LINEA_APT" | sudo tee "$LISTA" >/dev/null
  fi
  sudo apt-get update
  # CLOUDSDK_SKIP_PY_COMPILATION=1 acorta la instalacion (opcion documentada por Google)
  sudo env CLOUDSDK_SKIP_PY_COMPILATION=1 apt-get install -y "${faltan[@]}"
fi

echo "--- Verificacion ---"
if mostrar_versiones; then echo "SDK LISTO"; else echo "Hay herramientas sin instalar o que fallan: revisa las lineas [FALTA]" >&2; exit 1; fi
