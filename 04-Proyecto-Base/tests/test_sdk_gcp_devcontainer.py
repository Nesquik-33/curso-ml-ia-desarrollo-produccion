"""Pruebas estaticas del SDK de Google Cloud en el Codespace (T34): nada de esto necesita nube ni Docker.

Que vigilan: que los dos devcontainer son JSON validos; que el arranque por defecto (`.devcontainer/devcontainer.json` y
`postcreate.sh`) NO instala el SDK; que la configuracion aparte solo cambia el nombre y la orden posterior a la creacion;
que `deploy/gcp/instalar_sdk.sh` no lleva claves, correos ni rutas personales, es idempotente por construccion y tiene modo
`--comprobar`. La ejecucion real del script (apt) se prueba en un Codespace en T36: aqui solo se ejecuta `--comprobar` si hay bash POSIX.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
DC = RAIZ / '.devcontainer'
PRINCIPAL = DC / 'devcontainer.json'
CON_SDK = DC / 'gcp' / 'devcontainer.json'
SCRIPT = RAIZ / '04-Proyecto-Base' / 'deploy' / 'gcp' / 'instalar_sdk.sh'


def cargar(p):
    return json.loads(p.read_text(encoding='utf-8'))


def test_los_dos_devcontainer_son_json_valido():
    for p in (PRINCIPAL, CON_SDK):
        assert isinstance(cargar(p), dict), p


def test_el_arranque_por_defecto_no_instala_el_sdk():
    assert cargar(PRINCIPAL)['postCreateCommand'] == 'bash .devcontainer/postcreate.sh'
    for p in (PRINCIPAL, DC / 'postcreate.sh', DC / 'verificar.sh'):
        t = p.read_text(encoding='utf-8')
        assert 'instalar_sdk' not in t and 'google-cloud-cli' not in t, p


def test_la_configuracion_con_sdk_solo_cambia_nombre_y_orden_posterior():
    a, b = cargar(PRINCIPAL), cargar(CON_SDK)
    assert {k for k in a if a[k] != b.get(k)} | {k for k in b if k not in a} == {'name', 'postCreateCommand'}
    assert b['postCreateCommand'].startswith(a['postCreateCommand'])
    assert 'deploy/gcp/instalar_sdk.sh' in b['postCreateCommand']
    assert b['postCreateCommand'].rstrip().endswith('|| true'), 'un fallo del SDK no debe romper la creacion del Codespace'
    assert (RAIZ / '04-Proyecto-Base' / 'deploy' / 'gcp' / 'instalar_sdk.sh').exists()


def test_el_script_no_lleva_claves_correos_ni_rutas_personales():
    t = SCRIPT.read_text(encoding='utf-8')
    assert '\r' not in t, 'terminaciones LF'
    assert not re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', t), 'correo'
    assert not re.search(r'(?i)BEGIN (RSA |PRIVATE )|private_key|"type":\s*"service_account"|ya29\.|AIza[0-9A-Za-z_-]{20}', t), 'clave o token'
    assert not re.search(r'(?i)C:\\|/Users/|/home/\w+', t), 'ruta personal'
    assert 'SIN VERIFICAR' in t


def test_el_script_es_idempotente_y_tiene_modo_comprobar():
    t = SCRIPT.read_text(encoding='utf-8')
    assert t.startswith('#!/usr/bin/env bash') and 'set -euo pipefail' in t
    assert '--comprobar' in t and 'command -v' in t and 'grep -qsF' in t
    for paquete in ('google-cloud-cli', 'google-cloud-cli-gke-gcloud-auth-plugin'):
        assert paquete in t
    for orden in ('gcloud version', 'bq version', 'gcloud storage', 'kubectl version --client', 'gke-gcloud-auth-plugin --version'):
        assert orden in t


def _bash_posix():
    if sys.platform == 'win32':
        return None
    return shutil.which('bash')


@pytest.mark.skipif(_bash_posix() is None, reason='no hay bash POSIX (Windows): se prueba en el Codespace, T36')
def test_comprobar_se_ejecuta_sin_instalar_nada():
    bash = _bash_posix()
    assert subprocess.run([bash, '-n', str(SCRIPT)]).returncode == 0
    r = subprocess.run([bash, str(SCRIPT), '--comprobar'], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert 'gcloud version' in r.stdout
