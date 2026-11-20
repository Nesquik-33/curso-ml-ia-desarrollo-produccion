"""Pruebas del laboratorio de MLflow (sin navegador).

Qué vigilan: que index.html está al día con generar.py; 45 minutos en total; título, parte, minutos y notas en cada diapositiva;
que las órdenes citadas usan módulos y rutas que existen en el proyecto y los nombres que de verdad registra train.py; sin
recursos externos; que solo se citan las capturas previstas (o su recuadro «Captura pendiente»); el botón «⌂ S3»; que la guía
repite las mismas órdenes, el mismo fragmento de carga y las mismas salidas.
Se ejecutan solas (no junto con las de otros laboratorios: los archivos de prueba se llaman igual).
"""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
GUIA = AQUI / 'guia.md'

_spec = importlib.util.spec_from_file_location('generar_lab_mlflow', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

PERMITIDAS = {
    'm01-comprobar.webp', 'm02-arrancar.webp', 'm03-inicio.webp', 'm04-experimento.webp', 'm05-run-detalle.webp',
    'm06-comparar.webp', 'm07-artefactos.webp', 'm08-modelos.webp', 'm09-forzar.webp', 'm10-version2.webp', 'm11-cargar.webp',
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


def test_minutos_suman_45_y_cada_diapositiva_tiene_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 14 <= len(s) <= 18
    total = 0
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-D]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        total += int(m.group(1))
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 60, f'notas demasiado cortas en {t.group(1)}'
        assert '<h1>' in cuerpo
    assert total == 45 == G.DURACION


def test_minutos_por_parte():
    G.construir()
    por_parte = {}
    for s in G.SLIDES:
        por_parte[s['parte']] = por_parte.get(s['parte'], 0) + s['min']
    assert por_parte == {'A': 7, 'B': 4, 'C': 30, 'D': 4}


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html
    for ruta in re.findall(r'(?:src|href|data-src)="([^"#]+)"', html):
        assert not ruta.startswith(('http', '//')), ruta


def test_boton_s3_al_indice_de_la_sesion(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ S3' in html
    assert (AQUI.parent / 'index.html').exists()


def test_solo_las_capturas_previstas(html):
    assert set(G.CAPTURAS) == PERMITIDAS
    citadas = set(re.findall(r'img/(m\d\d-[a-z0-9-]+\.webp)', html))
    pendientes = set(re.findall(r'data-falta="([^"]+)"', html))
    assert citadas <= PERMITIDAS and pendientes <= PERMITIDAS
    assert citadas | pendientes == PERMITIDAS, 'cada captura prevista debe salir en alguna diapositiva'
    for nombre in citadas - pendientes:
        assert (AQUI / 'img' / nombre).exists(), nombre
    assert not re.findall(r'<img[^>]+src="(?!img/m\d\d-)', html), 'hay imágenes fuera de la lista'


def test_la_guia_cita_las_mismas_capturas(guia):
    assert set(re.findall(r'img/(m\d\d-[a-z0-9-]+\.webp)', guia)) == PERMITIDAS


def test_cada_orden_de_terminal_tiene_su_boton_de_copiar(html):
    for clave in ('ir', 'activar', 'comprobar', 'ui', 'train', 'forzar'):
        assert f'data-t="{G.esc(G.O[clave])}"' in html, clave
    assert f'data-t="{G.esc(G.CARGAR)}"' in html


def _textos_de_ordenes():
    return list(G.O.values()) + [G.CARGAR, G.UI_HOSTS]


def test_los_modulos_y_rutas_citados_existen():
    for texto in _textos_de_ordenes():
        for mod in re.findall(r'python -m ([a-z_][a-z0-9_.]*)', texto):
            if mod == 'mlflow':
                continue
            ruta = PROYECTO / Path(*mod.split('.'))
            assert ruta.with_suffix('.py').exists() or (ruta / '__main__.py').exists(), mod
    assert (PROYECTO / 'tests' / 'datos' / 'cliente_ejemplo.json').exists()
    assert 'tests/datos/cliente_ejemplo.json' in G.CARGAR
    assert (RAIZ / '01-Sesiones' / 'recap' / 'recap-01' / 'mlflow-paso-a-paso.md').exists()
    for opcion in ('--comprobar', '--port'):
        assert opcion in (PROYECTO / 'ia_mlops' / 'mlflow_ui.py').read_text(encoding='utf-8')
    assert '--forzar' in (PROYECTO / 'ia_mlops' / 'pipeline_train.py').read_text(encoding='utf-8')


def test_los_nombres_son_los_que_registra_train_py():
    sys.path.insert(0, str(PROYECTO))
    try:
        from ia_mlops import config, mlflow_ui
    finally:
        sys.path.remove(str(PROYECTO))
    assert config.EXPERIMENTO_MLFLOW == config.MODELO_REGISTRADO == 'retencion-90d'
    assert len(config.FEATURES) == 13
    assert callable(mlflow_ui.uri) and mlflow_ui.uri().startswith('sqlite:///')
    train = (PROYECTO / 'ia_mlops' / 'modeling' / 'train.py').read_text(encoding='utf-8')
    for parametro in ('modelo', 'ventana_objetivo_dias', 'n_variables', 'huella_datos'):
        assert f"log_param('{parametro}'" in train, parametro
    for metrica in ('auc', 'precision_media', 'tasa_base', 'aciertos_en_el_10_mejor'):
        assert f"'{metrica}'" in train, metrica
    assert "run_name=f'MEJOR-{mejor}'" in train and 'registered_model_name=config.MODELO_REGISTRADO' in train
    for etiqueta in ("('modelo', mejor)", "('huella_datos'", "('valid_auc'"):
        assert etiqueta in train, etiqueta


def test_la_guia_repite_las_ordenes_y_las_salidas(guia):
    for clave in ('ir', 'activar', 'comprobar', 'ui', 'ui5001', 'train', 'forzar', 'pipeline'):
        assert G.O[clave] in guia, clave
    assert G.CARGAR in guia and G.UI_HOSTS in guia
    for clave, salida in G.SALIDAS.items():
        for linea in salida.splitlines():
            if linea.strip():
                assert linea.strip() in guia, (clave, linea)


def test_sin_rutas_personales_ni_credenciales(html, guia):
    for texto in (html, guia, (AQUI / 'generar.py').read_text(encoding='utf-8')):
        assert 'C:\\Users' not in texto and 'AppData' not in texto
        assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
        assert not re.search(r'(token|password|contraseña)\s*[:=]', texto, re.I)
