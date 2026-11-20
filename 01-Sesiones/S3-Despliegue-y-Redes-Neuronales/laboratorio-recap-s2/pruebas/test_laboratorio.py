"""Pruebas del laboratorio-recap de S2 (sin navegador).

Qué vigilan: que index.html está al día con generar.py; 90 minutos en total; título, parte, minutos y notas en cada diapositiva;
que las órdenes citadas usan módulos y rutas que existen en el proyecto; sin recursos externos; que solo se citan las capturas
previstas (o su recuadro «Captura pendiente»); que la guía repite las mismas órdenes, el mismo fragmento de FS al vuelo y
las mismas salidas. Si existe la base del proyecto, ejecuta el fragmento de FS al vuelo y comprueba que dice True.
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
GUIA = AQUI / 'guia.md'

_spec = importlib.util.spec_from_file_location('generar_lab_recap_s2', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

PERMITIDAS = {
    'r01-codespace.webp', 'r02-pipeline.webp', 'r03-api-arrancada.webp', 'r04-puertos.webp', 'r05-docs.webp',
    'r06-predecir.webp', 'r07-lote.webp', 'r08-fs-al-vuelo.webp', 'r09-interfaz-13599.webp', 'r10-interfaz-variables.webp',
    'r11-interfaz-ejemplo.webp', 'r12-interfaz-corte.webp', 'r13-listo-503.webp',
}


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def guia():
    return GUIA.read_text(encoding='utf-8')


def secciones(texto):
    return re.findall(r'<section class="slide"([^>]*)>(.*?)</section>', texto, re.S)


def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_minutos_suman_90_y_cada_diapositiva_tiene_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 16 <= len(s) <= 22
    total = 0
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-E]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        total += int(m.group(1))
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 60, f'notas demasiado cortas en {t.group(1)}'
        assert '<h1>' in cuerpo
    assert total == 90 == G.DURACION


def test_tabla_del_plan_cuadra_con_los_minutos_por_parte():
    G.construir()
    por_parte = {}
    for s in G.SLIDES:
        por_parte[s['parte']] = por_parte.get(s['parte'], 0) + s['min']
    assert por_parte == {'A': 14, 'B': 29, 'C': 17, 'D': 25, 'E': 5}


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html
    for ruta in re.findall(r'(?:src|href|data-src)="([^"#]+)"', html):
        assert not ruta.startswith(('http', '//')), ruta


def test_solo_las_capturas_previstas(html):
    assert set(G.CAPTURAS) == PERMITIDAS
    citadas = set(re.findall(r'img/(r\d\d-[a-z0-9-]+\.webp)', html))
    pendientes = set(re.findall(r'data-falta="([^"]+)"', html))
    assert citadas <= PERMITIDAS and pendientes <= PERMITIDAS
    assert citadas | pendientes == PERMITIDAS, 'cada captura prevista debe salir en alguna diapositiva'
    for nombre in citadas - pendientes:
        assert (AQUI / 'img' / nombre).exists(), nombre
    assert not re.findall(r'<img[^>]+src="(?!img/r\d\d-)', html), 'hay imágenes fuera de la lista'


def test_la_guia_cita_las_mismas_capturas(guia):
    citadas = set(re.findall(r'img/(r\d\d-[a-z0-9-]+\.webp)', guia))
    assert citadas == PERMITIDAS


def test_cada_orden_tiene_su_boton_de_copiar(html):
    for clave, orden in G.O.items():
        if clave in ('ir', 'activar', 'ver'):
            continue
        assert f'data-t="{G.esc(orden)}"' in html, clave
    assert f'data-t="{G.esc(G.FS_AL_VUELO)}"' in html


def _textos_de_ordenes():
    return list(G.O.values()) + [G.FS_AL_VUELO]


def test_los_modulos_y_rutas_citados_existen():
    for texto in _textos_de_ordenes():
        for mod in re.findall(r'python -m ([a-z_][a-z0-9_.]*)', texto):
            if mod in ('uvicorn', 'json.tool'):
                continue
            ruta = PROYECTO / Path(*mod.split('.'))
            assert ruta.with_suffix('.py').exists() or (ruta / '__main__.py').exists(), mod
        for app in re.findall(r'(ia_mlops(?:\.[a-z_]+)+):app', texto):
            assert (PROYECTO / Path(*app.split('.'))).with_suffix('.py').exists(), app
        for archivo in re.findall(r'-d @([^\s;]+)', texto):
            assert (PROYECTO / archivo).exists(), archivo
    assert (PROYECTO / 'sql' / 'fs' / '02_poblar_fs.sql').exists()
    assert (PROYECTO / 'deploy' / 'docker' / 'compose.yaml').exists()
    assert (RAIZ / '01-Sesiones' / 'S2-API-y-Docker' / 'practica' / 'interfaz-de-consulta.md').exists()


def test_las_funciones_del_fragmento_existen():
    sys.path.insert(0, str(PROYECTO))
    try:
        from ia_mlops import config, explotacion
    finally:
        sys.path.remove(str(PROYECTO))
    assert hasattr(explotacion, 'variables_en_corte') and hasattr(explotacion, 'corte_por_defecto')
    assert len(config.FEATURES) == 13
    assert [s['desde'] for s in config.SEGMENTOS_RECOMPRA] == [0.70, 0.40, 0.0]


def test_la_guia_repite_las_ordenes_y_las_salidas(guia):
    for clave in ('preparar', 'api', 'salud', 'listo', 'modelo', 'predecir', 'lote', 'p422', 'interfaz', 'i_listo', 'i_salud_listo'):
        assert G.O[clave] in guia, clave
    assert G.FS_AL_VUELO in guia
    for clave in ('operacional', 'api', 'predecir', 'fs', 'i_listo', 'ejemplo', 'corte', 'parada'):
        for linea in G.SALIDAS[clave].splitlines():
            if '…' not in linea:
                assert linea.strip() in guia, (clave, linea)


def test_sin_rutas_personales_ni_gcp(html, guia):
    for texto in (html, guia):
        assert 'C:\\Users' not in texto and 'AppData' not in texto
        assert 'gcloud' not in texto


@pytest.mark.skipif(not (PROYECTO / 'data' / 'processed' / 'curso.db').exists(), reason='sin la base del proyecto (ejecuta el pipeline)')
def test_el_fragmento_de_fs_al_vuelo_da_true():
    cuerpo = G.FS_AL_VUELO.split('\n', 1)[1].rsplit('\nEOF', 1)[0]
    r = subprocess.run([sys.executable, '-'], input=cuerpo, capture_output=True, text=True, encoding='utf-8', cwd=PROYECTO, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    assert 'Iguales en el corte entrenado: True' in r.stdout
