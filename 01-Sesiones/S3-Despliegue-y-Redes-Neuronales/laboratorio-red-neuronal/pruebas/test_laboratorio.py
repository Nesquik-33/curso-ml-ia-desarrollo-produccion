"""Pruebas del laboratorio de red neuronal (sin navegador y sin importar torch).

Qué vigilan: index.html al día con generar.py; 30 minutos; título, parte, minutos y notas en cada diapositiva; solo las capturas
previstas (o su recuadro «Captura pendiente»); sin recursos externos; el botón «⌂ S3»; que red_gato_perro.py tiene las tres
subórdenes (leído con ast); que requisitos.txt fija las versiones; sin rutas personales ni credenciales.
Se ejecutan solas (no junto con las de otros laboratorios: los archivos de prueba se llaman igual).
"""
import ast
import importlib.util
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
SCRIPT = AQUI / 'red_gato_perro.py'

_spec = importlib.util.spec_from_file_location('generar_lab_red', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

PERMITIDAS = {'n01-instalar.webp', 'n02-datos.webp', 'n03-entrenar.webp', 'n04-mlflow.webp', 'n05-predecir.webp'}


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


def secciones(texto):
    return re.findall(r'<section class="slide"([^>]*)>(.*?)</section>', texto, re.S)


def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_minutos_suman_30_y_cada_diapositiva_tiene_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 10 <= len(s) <= 13
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
    assert total == 30 == G.DURACION


def test_solo_las_capturas_previstas(html):
    assert set(G.CAPTURAS) == PERMITIDAS
    citadas = set(re.findall(r'img/(n\d\d-[a-z0-9-]+\.webp)', html))
    pendientes = set(re.findall(r'data-falta="([^"]+)"', html))
    assert citadas <= PERMITIDAS and pendientes <= PERMITIDAS
    assert citadas | pendientes == PERMITIDAS, 'cada captura prevista debe salir en alguna diapositiva'
    for nombre in citadas - pendientes:
        assert (AQUI / 'img' / nombre).exists(), nombre
    assert not re.findall(r'<img[^>]+src="(?!img/n\d\d-)', html), 'hay imágenes fuera de la lista'


def test_la_guia_cita_las_mismas_capturas():
    guia = (AQUI / 'guia.md').read_text(encoding='utf-8')
    assert set(re.findall(r'img/(n\d\d-[a-z0-9-]+\.webp)', guia)) == PERMITIDAS


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html


def test_boton_s3_al_indice_de_la_sesion(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ S3' in html
    assert (AQUI.parent / 'index.html').exists()


def test_el_script_tiene_las_tres_subordenes_sin_importar_torch():
    arbol = ast.parse(SCRIPT.read_text(encoding='utf-8'))
    subordenes = {n.args[0].value for n in ast.walk(arbol)
                  if isinstance(n, ast.Call) and getattr(n.func, 'attr', '') == 'add_parser'
                  and n.args and isinstance(n.args[0], ast.Constant)}
    assert subordenes == {'datos', 'entrenar', 'predecir'}
    funciones = {n.name for n in arbol.body if isinstance(n, ast.FunctionDef)}
    assert {'orden_datos', 'orden_entrenar', 'orden_predecir', 'preparar_imagen', 'main'} <= funciones
    # torch solo se importa dentro de funciones: el script se puede leer sin tenerlo instalado
    arriba = [n for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert not any('torch' in (getattr(n, 'module', '') or '') or any('torch' in a.name for a in n.names) for n in arriba)
    texto = SCRIPT.read_text(encoding='utf-8')
    for clave in ("SEMILLA = 42", "PETS_URL = 'https://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz'",
                  "NOMBRE = 'gato-perro'", 'mlflow_ui.uri()', 'registered_model_name=NOMBRE', 'CC BY-SA 4.0'):
        assert clave in texto, clave


def test_requisitos_fijan_versiones():
    req = (AQUI / 'requisitos.txt').read_text(encoding='utf-8')
    assert '--extra-index-url https://download.pytorch.org/whl/cpu' in req
    for paquete in ('torch==', 'torchvision==', 'mlflow==3.18.0', 'scikit-learn==', 'pillow==', 'pandas=='):
        assert paquete in req, paquete


def test_las_ordenes_de_la_presentacion_estan_en_la_guia():
    guia = (AQUI / 'guia.md').read_text(encoding='utf-8')
    for orden in G.O.values():
        assert orden in guia, orden


def test_sin_rutas_personales_ni_credenciales(html):
    for texto in (html, (AQUI / 'guia.md').read_text(encoding='utf-8'), (AQUI / 'generar.py').read_text(encoding='utf-8'),
                  SCRIPT.read_text(encoding='utf-8')):
        assert 'C:\\Users' not in texto and 'AppData' not in texto
        assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
        assert not re.search(r'(token|password|contraseña)\s*[:=]', texto, re.I)
