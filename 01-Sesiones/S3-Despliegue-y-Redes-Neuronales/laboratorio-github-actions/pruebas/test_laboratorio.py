"""Pruebas del laboratorio de GitHub Actions de S3 (sin navegador ni GitHub).

Qué vigilan: que index.html está al día con generar.py; 90 minutos y cada diapositiva con título, parte, minutos y notas;
que el workflow es YAML válido, solo lee el repositorio, tiene tiempo máximo y solo se dispara en ramas lab/; que no choca con
los workflows del curso; que la rotura de una línea hace fallar la regla y el arreglo la devuelve; que las rutas citadas
existen; que las capturas son exactamente las de la lista; ⧉ en cada orden; sin recursos externos.
Ejecutar desde la raíz del repositorio:  python -m pytest 01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-github-actions/pruebas -q
"""
import ast
import importlib.util
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip('yaml')

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
WORKFLOWS = RAIZ / '.github' / 'workflows'

_spec = importlib.util.spec_from_file_location('generar_lab_actions', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

CAPTURAS = ['a01-rama.webp', 'a02-yaml.webp', 'a03-push.webp', 'a04-actions-lista.webp', 'a05-run-curso.webp', 'a06-run-verde.webp',
            'a07-rotura.webp', 'a08-run-rojo.webp', 'a09-log-error.webp', 'a10-arreglo.webp', 'a11-run-verde-otra-vez.webp', 'a12-historial.webp']


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def wf():
    return yaml.safe_load((AQUI / 'pruebas-proyecto.yml').read_text(encoding='utf-8'))


def disparadores(d):
    return d.get('on', d.get(True))          # PyYAML lee la clave «on» como True


def secciones(texto):
    return re.findall(r'<section class="slide"([^>]*)>(.*?)</section>', texto, re.S)


def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_noventa_minutos_y_cada_diapositiva_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 16 <= len(s) <= 22, len(s)
    total = 0
    for attrs, _ in s:
        assert re.search(r'data-part="[ABCDE]"', attrs) and re.search(r'data-title="[^"]+"', attrs), attrs[:80]
        notas = re.search(r'data-notes="([^"]*)"', attrs).group(1)
        assert len(notas) > 80, f'notas del ponente demasiado cortas: {attrs[:80]}'
        total += int(re.search(r'data-min="(\d+)"', attrs).group(1))
    assert total == 90, total


def test_el_workflow_es_valido_minimo_y_con_tiempo_maximo(wf):
    assert wf['name'] == 'Pruebas del proyecto'
    on = disparadores(wf)
    assert on['push']['branches'] == ['lab/**'] and 'workflow_dispatch' in on
    assert 'pull_request' not in on
    assert wf['permissions'] == {'contents': 'read'}
    job = wf['jobs']['pruebas']
    assert job['runs-on'] == 'ubuntu-latest' and 0 < job['timeout-minutes'] <= 15
    assert job['defaults']['run']['working-directory'] == '04-Proyecto-Base'
    pasos = job['steps']
    assert [p.get('uses', '').split('@')[0] for p in pasos[:2]] == ['actions/checkout', 'actions/setup-python']
    assert pasos[1]['with']['python-version'] == '3.11' and pasos[1]['with']['cache'] == 'pip'
    instalar, probar = pasos[2]['run'], pasos[3]['run']
    assert 'pip install -r requirements-dev.txt' in instalar and 'pip install -e . --no-deps' in instalar
    assert probar.startswith('python -m pytest') and probar.split()[-3:] == G.PRUEBAS


def test_las_pruebas_y_archivos_que_usa_existen(wf):
    for p in G.PRUEBAS + ['tests/conftest.py', 'requirements-dev.txt', 'requirements-api.txt', 'pyproject.toml',
                          'ia_mlops/config.py', 'data/raw/muestra_online_retail_ii.csv', 'deploy/github-actions/ci.yml']:
        assert (PROYECTO / p).is_file(), p
    # la caché de pip apunta a archivos que existen
    patron = wf['jobs']['pruebas']['steps'][1]['with']['cache-dependency-path']
    assert list(RAIZ.glob(patron)), patron
    # las tres pruebas no están marcadas «lento» ni «gcp» (no necesitan cuadernos ni GCP)
    for p in G.PRUEBAS:
        texto = (PROYECTO / p).read_text(encoding='utf-8')
        assert 'mark.lento' not in texto and 'mark.gcp' not in texto, p
    for ruta in ('01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-github-actions/pruebas-proyecto.yml',):
        assert (RAIZ / ruta).is_file(), ruta


def test_no_choca_con_los_workflows_del_curso():
    """En una rama lab/ con cambios solo en .github/workflows/pruebas-proyecto.yml y 04-Proyecto-Base/ia_mlops/config.py,
    ningún otro workflow debe dispararse por push."""
    for archivo in WORKFLOWS.glob('*.yml'):
        on = disparadores(yaml.safe_load(archivo.read_text(encoding='utf-8')))
        push = on.get('push') if isinstance(on, dict) else None
        if not push:
            continue
        ramas = push.get('branches')
        if ramas is not None:
            assert not any(r.startswith('lab') or r in ('**', '*') for r in ramas), archivo.name
            continue
        rutas = push.get('paths') or []
        assert rutas, f'{archivo.name}: push sin ramas ni rutas se dispararía también en lab/'
        assert not any(r.startswith(('04-Proyecto-Base/ia_mlops', '.github/workflows/pruebas-proyecto')) or r in ('**', '*') for r in rutas), archivo.name


def _segmento_de():
    """La función real de ia_mlops/interfaz/consulta.py, sin importar el paquete (que carga el modelo y la API)."""
    arbol = ast.parse((PROYECTO / 'ia_mlops' / 'interfaz' / 'consulta.py').read_text(encoding='utf-8'))
    funcion = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == 'segmento_de')
    espacio = {}
    exec(compile(ast.Module(body=[funcion], type_ignores=[]), 'consulta.py', 'exec'), espacio)
    return espacio['segmento_de']


def _segmentos(texto_config):
    arbol = ast.parse(texto_config)
    nodo = next(n for n in arbol.body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'SEGMENTOS_RECOMPRA')
    return ast.literal_eval(nodo.value)


def test_la_rotura_cambia_una_linea_y_rompe_la_regla_y_el_arreglo_la_devuelve():
    config = (PROYECTO / 'ia_mlops' / 'config.py').read_text(encoding='utf-8')
    assert config.count("'desde': 0.70") == 1          # el sed solo puede cambiar una línea
    assert G.ROTURA == "sed -i \"s/'desde': 0.70/'desde': 0.75/\" 04-Proyecto-Base/ia_mlops/config.py"
    roto = config.replace("'desde': 0.70", "'desde': 0.75")
    distintas = [(a, b) for a, b in zip(config.splitlines(), roto.splitlines()) if a != b]
    assert len(distintas) == 1
    # lo que comprueba la prueba del proyecto (tests/test_interfaz.py::test_la_regla_de_negocio)
    prueba = (PROYECTO / 'tests' / 'test_interfaz.py').read_text(encoding='utf-8')
    assert "def test_la_regla_de_negocio" in prueba and "(0.99, 0.70, 0.69, 0.40, 0.39, 0.0)" in prueba
    assert "['alta', 'alta', 'media', 'media', 'baja', 'baja']" in prueba
    segmento_de = _segmento_de()
    probs = (0.99, 0.70, 0.69, 0.40, 0.39, 0.0)
    bien = [segmento_de(p, _segmentos(config))['segmento'] for p in probs]
    mal = [segmento_de(p, _segmentos(roto))['segmento'] for p in probs]
    assert bien == ['alta', 'alta', 'media', 'media', 'baja', 'baja']
    assert mal == ['alta', 'media', 'media', 'media', 'baja', 'baja']     # «At index 1 diff: 'media' != 'alta'»
    assert "At index 1 diff: 'media' != 'alta'" in G.SALIDA_ROTA


def test_las_capturas_son_las_de_la_lista(html):
    assert list(G.CAPTURAS) == CAPTURAS
    citadas = re.findall(r'<figure class="cap" data-img="([^"]+)"', html)
    assert sorted(citadas) == sorted(CAPTURAS), 'cada captura se cita exactamente una vez'
    for nombre in CAPTURAS:
        if (AQUI / 'img' / nombre).is_file():
            assert f'src="img/{nombre}"' in html and f'data-src="img/{nombre}"' in html, nombre
        else:
            assert f'<span class="mono">img/{nombre}</span>' in html, nombre
    en_disco = {p.name for p in (AQUI / 'img').glob('*') if p.is_file() and p.name != '.gitkeep'}
    assert en_disco <= set(CAPTURAS), f'archivos en img/ que no están en la lista: {en_disco - set(CAPTURAS)}'
    assert set(re.findall(r'src="img/([^"]+)"', html)) <= en_disco


def test_cada_orden_tiene_su_boton_de_copiar_y_el_yaml_se_copia_entero(html):
    ordenes = re.findall(r'<div class="tln"><span class="ps">\$</span> <code>(.*?)</code><button class="cp" data-t="(.*?)"', html)
    assert len(ordenes) >= 15
    for visible, copiar in ordenes:
        assert visible == copiar
    textos = {o for o, _ in ordenes}
    import html as h
    for orden in ('git switch -c lab/actions-s3', 'git push -u origin lab/actions-s3', G.ROTURA, 'git revert --no-edit HEAD',
                  'git push origin --delete lab/actions-s3'):
        assert h.escape(orden, quote=True) in textos, orden
    yml = h.escape((AQUI / 'pruebas-proyecto.yml').read_text(encoding='utf-8'), quote=True)
    assert f'data-t="{yml}">Copiar el archivo</button>' in html
    assert '<a id="bhome" href="../index.html"' in html


def test_la_guia_lleva_el_mismo_yaml_y_las_mismas_ordenes():
    guia = (AQUI / 'guia.md').read_text(encoding='utf-8')
    bloque = re.search(r'```yaml\n(.*?)```', guia, re.S).group(1)
    assert yaml.safe_load(bloque) == yaml.safe_load((AQUI / 'pruebas-proyecto.yml').read_text(encoding='utf-8'))
    for trozo in (G.ROTURA, 'git revert --no-edit HEAD', 'git push -u origin lab/actions-s3', 'git push origin --delete lab/actions-s3',
                  "At index 1 diff: 'media' != 'alta'"):
        assert trozo in guia, trozo
    for nombre in CAPTURAS:
        assert nombre.removesuffix('.webp') in guia, nombre


def test_sin_recursos_externos(html):
    assert not re.search(r'<(script|link|img|iframe)\b[^>]*\b(src|href)="https?://', html)
    assert '@import' not in html and 'url(http' not in html
