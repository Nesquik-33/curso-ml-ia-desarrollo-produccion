"""Pruebas de coherencia de la tarea S3 (avance 3), su rúbrica, la evidencia, la hoja de GCP, el guion y el checklist.

Ejecutar:  python -m pytest 01-Sesiones/S3-Despliegue-y-Redes-Neuronales/tarea/pruebas -q
No necesitan Internet. Mismo patrón que las de S1 y S2: pesos 20/40/40 que suman 100 y entrega a las 10:00 del miércoles de S4.
"""
import datetime
import re
from pathlib import Path

import pytest

S3 = Path(__file__).resolve().parents[2]
RAIZ = S3.parents[1]
TAREA = S3 / 'tarea' / 'README.md'
RUBRICA = S3 / 'tarea' / 'rubrica.md'
EVIDENCIA = S3 / 'evidencias' / 'plantilla-avance-3.md'
GCP = S3 / 'preparar-gcp-para-s4.md'
GUION = S3 / 'guion.md'
CHECKLIST = S3 / 'checklist.md'
README = S3 / 'README.md'
ALUMNO = RAIZ / '02-Proyecto-Transversal' / 'alumno'
DOCS = [TAREA, RUBRICA, EVIDENCIA, GCP, GUION, CHECKLIST, README]
LABORATORIOS = ('laboratorio-recap-s2/', 'laboratorio-github-actions/')   # los hace otro agente; se comprueban aparte
S4 = datetime.date(2026, 11, 25)   # calendario del instructor (10/11/2026)


def leer(ruta):
    return ruta.read_text(encoding='utf-8').replace(' ', ' ')


def pesos_de(ruta):
    filas = re.findall(r'^\| \*\*([^*|]+)\*\* \| (\d+) \|', leer(ruta), flags=re.M)
    return [(n.strip(), int(p)) for n, p in filas]


def test_la_rubrica_pesa_20_40_40_y_suma_100_como_s1_s2_y_la_de_avance():
    esperado = [('Reproducibilidad', 20), ('Técnica', 40), ('Análisis y decisión', 40)]
    assert pesos_de(RUBRICA) == esperado
    assert sum(p for _, p in pesos_de(RUBRICA)) == 100
    for otra in [RAIZ / '01-Sesiones' / 'S1-Datos-y-Entrenamiento' / 'tarea' / 'rubrica.md',
                 RAIZ / '01-Sesiones' / 'S2-API-y-Docker' / 'tarea' / 'rubrica.md', ALUMNO / 'rubrica-avance.md']:
        assert pesos_de(otra) == esperado, otra


def test_los_niveles_cubren_los_pesos_de_cada_criterio():
    t = leer(RUBRICA)
    assert '| Sobresaliente | 18–20' in t and '36–40' in t and '| Insuficiente | 0–7 | 0–15 | 0–15 |' in t


def test_la_rubrica_tiene_los_topes_pedidos_y_marca_lo_nuevo_como_propuesta():
    t = leer(RUBRICA)
    assert re.search(r'credencial o un token en el repositorio.*la técnica no supera 25', t)
    assert re.search(r'workflow que nunca se ejecutó.*solo se demuestra con capturas.*la reproducibilidad no supera 8', t)
    assert re.search(r'Presentar como hecho lo que no se hizo.*el análisis no supera 20', t)
    assert t.count('propuesta') >= 3


def test_la_entrega_es_el_miercoles_de_s4_a_las_10_hora_de_peru():
    assert S4.weekday() == 2, 'S4 no cae en miércoles'
    for ruta in [TAREA, EVIDENCIA]:
        t = leer(ruta)
        assert 'miércoles 25 de noviembre' in t and '10:00' in t and 'hora de Perú' in t, ruta.name
    assert 'mié 25 nov, 10:00' in leer(ALUMNO / 'tu-caso-bank-marketing.md')


def test_se_entrega_con_el_formulario_sin_enlaces_inventados():
    for ruta in [TAREA, EVIDENCIA, GUION]:
        t = leer(ruta)
        assert 'ormulario de Google' in t, ruta.name
        assert not re.search(r'forms\.gle|docs\.google\.com/forms', t)


def test_la_tarea_es_actions_mas_gcp_preparado_y_no_la_migracion():
    t = leer(TAREA)
    assert t.startswith('# Tarea S3 · Tus pruebas en GitHub Actions')
    for pieza in ['prueba propia significativa', 'rojo', 'verde', 'enlaces a las dos ejecuciones', 'presupuesto con alertas',
                  'cuenta de Google', 'Activar Google Cloud', 'No crees nada más', 'la migración a GCP pasa a **S4**', 'rama `avance-3`']:
        assert pieza in t, pieza
    assert 'plantilla-migracion-gcp' not in t and 'datos.sh --ejecutar' not in t


def test_la_evidencia_pide_lo_que_piden_tarea_y_rubrica():
    t = leer(EVIDENCIA)
    for pieza in ['## 2. El workflow', '## 3. Mis pruebas', '## 4. Del rojo al verde', '| Rojo |', '| Verde (arreglo) |',
                  'Verde al entregar', '## 5. Una decisión', '## 6. Google Cloud activado', 'Ningún recurso creado',
                  'correo tapado', '## 7. Lo que no pude hacer', 'https://doi.org/10.24432/C5K306']:
        assert pieza in t, pieza


def test_el_guion_suma_240_minutos_en_bloques_seguidos_de_10_a_14():
    filas = re.findall(r'^\| (\d\d):(\d\d)–(\d\d):(\d\d) \| (\d+) \|', leer(GUION), flags=re.M)
    assert [int(f[4]) for f in filas] == [10, 70, 35, 15, 70, 20, 20]   # bienvenida, recap, MLflow, pausa, Actions, red neuronal, GCP+tarea
    assert sum(int(f[4]) for f in filas) == 240
    reloj = 10 * 60
    for h1, m1, h2, m2, mins in filas:
        assert int(h1) * 60 + int(m1) == reloj
        reloj += int(mins)
        assert int(h2) * 60 + int(m2) == reloj
    assert reloj == 14 * 60


def test_el_guion_trae_los_fallos_en_directo_pedidos():
    t = leer(GUION)
    for sintoma in ['El Codespace no arranca', 'Falta `curso.db`', 'python -m ia_mlops.operacional', 'python -m ia_mlops.pipeline',
                    'Puerto ocupado', 'Actions desactivado en el *fork*', 'se queda en cola']:
        assert sintoma in t, sintoma


def test_la_hoja_de_gcp_no_da_cifras_ni_textos_de_consola():
    t = leer(GCP)
    assert 'sin verificar; consulta la página oficial' in t
    assert 'avisa; no corta el gasto' in t and 'compruébalo en la documentación vigente' in t
    assert '(../../03-Entorno/guias/sdk-google-cloud-vscode-y-codespaces.md)' in t
    assert not re.search(r'(US\$|USD|\$\s?\d|\d\s?\$|€|S/\s?\d|\d+\s?(dólares|soles|euros))', t), 'hay una cifra de dinero'
    assert not re.search(r'\b\d+\s?(días|horas)\s+(gratis|de prueba)', t)


@pytest.mark.parametrize('ruta', DOCS + [ALUMNO / 'rubrica-avance.md', ALUMNO / 'plantilla-avance.md', ALUMNO / 'tu-caso-bank-marketing.md'],
                         ids=lambda r: r.name)
def test_sin_correos_credenciales_ni_rutas_personales(ruta):
    t = leer(ruta)
    assert not re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', t), 'hay un correo'
    assert not re.search(r'AIza[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z]{20,}|"private_key"', t), 'parece una credencial'
    assert not re.search(r'[A-Z]:\\Users\\|/home/\w+', t), 'hay una ruta personal'


def enlaces(ruta):
    return [d for d in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', leer(ruta)) if not d.startswith(('http://', 'https://'))]


@pytest.mark.parametrize('ruta', DOCS + [ALUMNO / 'rubrica-avance.md', ALUMNO / 'plantilla-avance.md', ALUMNO / 'tu-caso-bank-marketing.md'],
                         ids=lambda r: r.name)
def test_los_enlaces_relativos_existen(ruta):
    for destino in enlaces(ruta):
        if destino.startswith(LABORATORIOS) or '/laboratorio-' in destino:
            continue
        assert (ruta.parent / destino).resolve().exists(), f'{ruta.name}: «{destino}» no existe'


def test_los_enlaces_a_los_laboratorios_existen_cuando_esten():
    faltan = sorted({d for r in DOCS for d in enlaces(r) if (d.startswith(LABORATORIOS) or '/laboratorio-' in d)
                     and not (r.parent / d).resolve().exists()})
    if faltan:
        pytest.skip('laboratorios aún sin publicar: ' + ', '.join(faltan))


def test_el_caso_propio_concreta_el_avance_3_y_dice_que_la_migracion_pasa_a_s4():
    r = leer(ALUMNO / 'rubrica-avance.md')
    assert '**3 · GCP preparado y pruebas en GitHub Actions**' in r and 'la migración a GCP pasa a S4' in r
    assert 'Se concretará al preparar S3' not in r
    p = leer(ALUMNO / 'plantilla-avance.md')
    assert '### Avance 3 · pruebas en GitHub Actions y GCP preparado para S4' in p and 'La migración a GCP pasa a S4' in p
    h = leer(ALUMNO / 'tu-caso-bank-marketing.md')
    assert 'La migración a GCP pasa a S4' in h and 'Migración a GCP y despliegue: inventario' not in h


def test_el_readme_avisa_del_cambio_de_plan():
    t = leer(README)
    assert 'GCP en vivo pasa a S4' in t and 'plan previo' in t and '00-Planificacion/s3/' in t
