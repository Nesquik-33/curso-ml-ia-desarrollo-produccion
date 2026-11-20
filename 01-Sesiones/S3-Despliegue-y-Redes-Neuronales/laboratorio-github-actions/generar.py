"""Genera la presentación «Laboratorio de GitHub Actions» de S3 (index.html, junto a este archivo).

Romper y arreglar: en su fork y su Codespace, cada persona crea la rama lab/actions-s3, añade el workflow
pruebas-proyecto.yml, lo ve en verde, rompe una prueba a propósito (rojo), lee el registro y lo arregla (verde).

Mismo manejo que las presentaciones de S2 (← → · O índice · S notas · F pantalla completa · Esc), con fondo blanco.
Cada orden lleva ⧉ para copiarla. Las capturas se leen de img/ con los nombres de CAPTURAS; si falta alguna,
se dibuja un recuadro «Captura pendiente» (no falla). Al añadir capturas, se vuelve a ejecutar este script.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
WORKFLOW = AQUI / 'pruebas-proyecto.yml'
FECHA = '20/11/2026'
RAMA = 'lab/actions-s3'
DESTINO = '.github/workflows/pruebas-proyecto.yml'
PRUEBAS = ['tests/test_raw_y_master.py', 'tests/test_fs_y_ml.py', 'tests/test_interfaz.py']

# Capturas que hace el profesor en su Codespace (webp). Nombre -> qué muestra (texto alternativo).
CAPTURAS = {
    'a01-rama.webp': 'Terminal: crear la rama lab/actions-s3 y el archivo del workflow',
    'a02-yaml.webp': 'El YAML del workflow abierto en el editor del Codespace',
    'a03-push.webp': 'Terminal: git push -u origin lab/actions-s3',
    'a04-actions-lista.webp': 'Pestaña Actions con el run de «Pruebas del proyecto»',
    'a05-run-curso.webp': 'El run en curso: el job «pruebas» y sus pasos',
    'a06-run-verde.webp': 'El run terminado en verde',
    'a07-rotura.webp': 'Terminal: el cambio de una línea (sed), git diff y el push',
    'a08-run-rojo.webp': 'El run en rojo',
    'a09-log-error.webp': 'Registro del paso «Ejecutar las pruebas» con la prueba que falla',
    'a10-arreglo.webp': 'Terminal: git revert y el push del arreglo',
    'a11-run-verde-otra-vez.webp': 'El run del arreglo, en verde otra vez',
    'a12-historial.webp': 'Lista de runs del workflow: verde, rojo y verde',
}

# Salida real de la prueba rota, en local (Windows, entorno env-ia-mlops, 20/11/2026), con el cambio de la rotura simulado.
SALIDA_ROTA = """FAILED tests/test_interfaz.py::test_la_regla_de_negocio
E       AssertionError: assert ['alta', 'med...baja', 'baja'] == ['alta', 'alt...baja', 'baja']
E         At index 1 diff: 'media' != 'alta'"""

ROTURA = "sed -i \"s/'desde': 0.70/'desde': 0.75/\" 04-Proyecto-Base/ia_mlops/config.py"

PARTES = {'A': 'Qué es CI', 'B': 'El workflow', 'C': 'Verde', 'D': 'Rojo', 'E': 'Arreglo y cierre'}


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código` y **negrita** a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])', r'<i>\1</i>', t)


def term(titulo, lineas):
    """Terminal con una orden por línea y su botón ⧉. Las líneas que empiezan por # son comentarios (no se copian)."""
    filas = []
    for l in lineas:
        if l.startswith('#'):
            filas.append(f'<div class="tln c">{esc(l)}</div>')
        else:
            filas.append(f'<div class="tln"><span class="ps">$</span> <code>{esc(l)}</code><button class="cp" data-t="{esc(l)}" title="Copiar">⧉</button></div>')
    todo = '\n'.join(l for l in lineas if not l.startswith('#'))
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em><button class="cp cpall" data-t="{esc(todo)}">Copiar todo</button></div>'
            f'<div class="tls">{"".join(filas)}</div></div>')


def yaml_texto():
    return WORKFLOW.read_text(encoding='utf-8')


def yaml_sin_comentarios():
    """El YAML sin líneas de comentario ni comentarios al final de línea: lo que se proyecta (el botón copia el archivo entero)."""
    salida = []
    for l in yaml_texto().splitlines():
        if l.lstrip().startswith('#'):
            continue
        salida.append(re.sub(r'\s+#\s.*$', '', l))
    texto = '\n'.join(salida).strip('\n')
    return re.sub(r'\n{3,}', '\n\n', texto)


def caja_yaml():
    """El YAML en dos columnas (cabecera y job | pasos) para que quepa entero a un tamaño legible."""
    texto = yaml_sin_comentarios()
    corte = texto.index('    steps:')
    izq, der = texto[:corte].rstrip('\n'), texto[corte:]

    def lineas(t):
        # cada línea conserva su sangría; si no cabe, continúa con sangría colgante (no se confunde con otro nivel)
        out = []
        for l in t.split('\n'):
            n = len(l) - len(l.lstrip(' '))
            out.append(f'<span class="yl" style="padding-left:{n + 3}ch;text-indent:-3ch">{esc(l.strip()) or "&nbsp;"}</span>')
        return ''.join(out)
    return (f'<div class="term yaml"><div class="bar"><em>{esc(DESTINO)}</em><button class="cp cpall" data-t="{esc(yaml_texto())}">Copiar el archivo</button></div>'
            f'<div class="yml2"><div class="yml">{lineas(izq)}</div><div class="yml">{lineas(der)}</div></div></div>')


def cap(nombre, alto=None):
    """Una captura (clic = ampliar) o, si aún no está en img/, el recuadro «Captura pendiente»."""
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    if (AQUI / 'img' / nombre).is_file():
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {esc(alt)}</figcaption></figure>')
    alto_p = f' style="min-height:{min(alto or 200, 260)}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"{alto_p}><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(alt)}</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(alt)}</figcaption></figure>')


LUPA = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12.5 12.5 L18 18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'


def rotulo_capturas(nombres):
    hay = [n for n in nombres if (AQUI / 'img' / n).is_file()]
    if len(hay) == len(nombres):
        return f'<p class="small rot"><span class="tag ok">Captura real</span> Codespace y cuenta del profesor · rama <span class="mono">{RAMA}</span> · {FECHA}</p>'
    return '<p class="small rot"><span class="tag warn">Captura pendiente</span> las capturas reales de este paso se añaden en <span class="mono">img/</span></p>'


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def mira(items, titulo='Qué debes ver'):
    return f'<div class="card mira"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def tabla(cab, filas):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


SLIDES = []


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    SLIDES.append(f'<section class="slide"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(kick)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')


def svg_ci():
    cajas = [('git push', 'desde tu Codespace'), ('GitHub', 'mira on: y elige el workflow'), ('Runner Linux nuevo', 'checkout · Python · pip · pytest')]
    g = ['<defs><marker id="fci" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    for i, (t, s) in enumerate(cajas):
        x = 10 + i * 250
        g.append(f'<rect x="{x}" y="50" width="210" height="80" rx="12" class="nodo"/><text x="{x + 105}" y="84" class="t1">{esc(t)}</text><text x="{x + 105}" y="108" class="t2">{esc(s)}</text>')
        if i:
            g.append(f'<path d="M{x - 38} 90 L{x - 4} 90" class="fl" marker-end="url(#fci)"/>')
    g.append('<path d="M720 90 L770 50" class="fl" marker-end="url(#fci)"/><path d="M720 90 L770 130" class="fl" marker-end="url(#fci)"/>')
    g.append('<rect x="774" y="20" width="126" height="52" rx="10" class="nodo ok"/><text x="837" y="52" class="t1 tok">verde</text>')
    g.append('<rect x="774" y="108" width="126" height="52" rx="10" class="nodo mal"/><text x="837" y="140" class="t1 tmal">rojo + registro</text>')
    return f'<svg viewBox="0 0 910 180" role="img" aria-label="Del push al resultado">{"".join(g)}</svg>'


def svg_anatomia():
    return '''<svg viewBox="0 0 560 300" role="img" aria-label="Workflow, job y pasos">
<rect x="6" y="6" width="548" height="288" rx="14" class="nodo"/><text x="20" y="32" class="t1" text-anchor="start">workflow · pruebas-proyecto.yml</text>
<text x="20" y="54" class="t2" text-anchor="start">on: push a lab/** · permissions: contents: read</text>
<rect x="26" y="70" width="508" height="210" rx="12" class="nodo job"/><text x="40" y="94" class="t1" text-anchor="start">job «pruebas» · runs-on: ubuntu-latest · timeout 10 min</text>
<rect x="46" y="110" width="468" height="32" rx="8" class="paso"/><text x="60" y="131" class="t2" text-anchor="start">1 · Descargar el repositorio (actions/checkout)</text>
<rect x="46" y="150" width="468" height="32" rx="8" class="paso"/><text x="60" y="171" class="t2" text-anchor="start">2 · Preparar Python 3.11 (actions/setup-python, caché de pip)</text>
<rect x="46" y="190" width="468" height="32" rx="8" class="paso"/><text x="60" y="211" class="t2" text-anchor="start">3 · Instalar dependencias (pip install …)</text>
<rect x="46" y="230" width="468" height="32" rx="8" class="paso"/><text x="60" y="251" class="t2" text-anchor="start">4 · Ejecutar las pruebas (python -m pytest -v …)</text>
</svg>'''


# =====================================================================================================================================
# Contenido
# =====================================================================================================================================
def construir():
    SLIDES.clear()

    # ---------------------------------------------------------------- A · Qué es CI
    slide('A', 1, 'Portada', 'S3 · ML e IA: de desarrollo a producción · 11:55–13:25 (hora de Perú)', 'Laboratorio de GitHub Actions: romper y arreglar', f'''
<div class="cover">
 <p class="sub">En tu fork y tu Codespace: un workflow que ejecuta las pruebas del proyecto en cada <span class="mono">git push</span>. Lo verás en verde, lo romperás a propósito, leerás el registro y lo devolverás al verde.</p>
 <div class="chips"><span class="tag">90 min</span><span class="tag">rama <span class="mono">{RAMA}</span></span><span class="tag">Codespace</span><span class="tag">sin GCP</span></div>
 <div class="card" style="margin-top:22px"><h3>Cómo seguirla</h3><p class="small">Cada orden lleva <b>⧉</b> para copiarla en la terminal del Codespace. <b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas · <b>F</b> pantalla completa · clic en una captura para ampliarla y <b>Esc</b> para cerrarla. Todo está también en texto en <span class="mono">guia.md</span>, junto a esta presentación.</p></div>
</div>''',
          'Laboratorio de 90 minutos. En S2 no dimos GitHub Actions: hoy es la primera vez que lo ven. Formato romper y arreglar: lo importante no es escribir YAML de memoria, sino entender qué hace cada línea, leer un registro rojo y arreglar el código sin borrar la prueba. Que cada persona tenga abierto su Codespace de su fork, en develop. Publicar imágenes y desplegar es de S4: hoy solo pruebas.')

    slide('A', 2, 'El plan', 'Lo que vas a hacer', 'Verde → rojo → verde, en ocho pasos', '''
<div class="grid2">
 <div class="card"><h3>Los pasos</h3><ol class="ol">
  <li>Crear la rama <span class="mono">lab/actions-s3</span></li><li>Añadir <span class="mono">.github/workflows/pruebas-proyecto.yml</span></li>
  <li><span class="mono">git push</span></li><li>Ver el run <b class="okc">en verde</b> en la pestaña <b>Actions</b></li>
  <li>Romper una regla con un cambio de <b>una línea</b></li><li>Ver el run <b class="malc">en rojo</b> y leer el registro</li>
  <li>Arreglarlo con <span class="mono">git revert</span></li><li>Ver el run <b class="okc">en verde</b> otra vez y el historial</li></ol></div>
 <div class="col">
  <div class="card"><h3>Al terminar sabrás</h3>''' + lista([
        'Qué es **CI** (integración continua) y para qué sirve.',
        'Leer un workflow: **cuándo** se dispara, **dónde** corre, **qué** pasos hace.',
        'Encontrar en el registro **qué prueba** falló y **por qué**.',
        'Arreglar **el código**, no la prueba.']) + '''</div>
  <div class="callout">Hoy el workflow solo <b>comprueba</b>. Construir y publicar la imagen y desplegar con aprobación es <b>S4</b>.</div>
 </div></div>''',
          'Enseñe el mapa completo antes de empezar para que nadie se pierda. Los pasos 1 a 4 son la parte verde, 5 y 6 la roja, 7 y 8 el arreglo. Insista en la última línea: no hay despliegue hoy, ni GCP. Si alguien llega tarde, puede seguir la guía de texto, guia.md, que tiene los mismos pasos.')

    slide('A', 5, 'Qué es CI', 'Concepto · en un minuto', '**CI**: cada cambio se comprueba solo', f'''
<div class="card">{svg_ci()}</div>
<div class="grid3" style="margin-top:14px">
 <div class="card"><h3>CI</h3><p class="small"><b>Continuous Integration</b>, integración continua: cada cambio que subes se comprueba <b>solo</b>, en una máquina <b>limpia</b>, con las mismas órdenes de siempre.</p></div>
 <div class="card"><h3>Sin CI</h3><p class="small">«En mi máquina funciona». Las pruebas se pasan cuando alguien se acuerda, y un fallo aparece semanas después sin saber qué cambio lo trajo.</p></div>
 <div class="card"><h3>Con CI</h3><p class="small">Cada <span class="mono">git push</span> deja un resultado <b class="okc">verde</b> o <b class="malc">rojo</b>, con su registro, visible para todo el equipo. Sabes <b>qué cambio</b> rompió qué.</p></div>
</div>''',
          'Explique CI en un minuto con el dibujo: haces push, GitHub mira el workflow, una máquina Linux nueva descarga el repositorio, instala todo desde cero y pasa las pruebas. Si todas pasan, verde; si alguna falla, rojo y un registro que dice cuál. La palabra clave es máquina limpia: no tiene nada de tu Codespace, así que si pasa ahí, no depende de lo que tú tengas instalado. Enlace con S2: el problema de en mi máquina funciona.')

    slide('A', 4, 'Vocabulario de Actions', 'Concepto · seis palabras', 'Workflow, disparador, runner, job, paso y run', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="card">''' + tabla(['Palabra', 'Qué es'], [
        ['**workflow**', 'archivo YAML en `.github/workflows/`: **cuándo** y **qué** ejecutar'],
        ['**disparador** (`on:`)', 'el suceso que lo pone en marcha: un `push`, un *pull request*, un botón'],
        ['**runner**', 'la máquina que presta GitHub; aquí, Linux nueva y vacía'],
        ['**job**', 'un trabajo del workflow; corre en un runner'],
        ['**paso** (*step*)', 'cada orden o acción del job, en orden; si uno falla, el job se para en rojo'],
        ['**run**', 'una ejecución concreta, con su registro']]) + f'''</div>
 <div class="card">{svg_anatomia()}</div>
</div>''',
          'Seis palabras que verán escritas en la pestaña Actions. Señale el dibujo: un workflow contiene un job, el job corre en un runner y tiene cuatro pasos. Un run es cada vez que se ejecuta. YAML es solo el formato del archivo: listas y claves con sangría. La sangría es la sintaxis: dos espacios por nivel, nunca tabuladores.')

    # ---------------------------------------------------------------- B · El workflow
    slide('B', 5, 'El workflow completo', 'El archivo que vas a copiar', 'El workflow entero, en una pantalla', f'''
<div class="split" style="grid-template-columns:1.45fr .55fr">
 {caja_yaml()}
 <div class="col">
  <div class="card"><h3>Dónde va</h3><p class="small">En la raíz de tu repositorio: <span class="mono">{DESTINO}</span>. Con el punto delante de <span class="mono">.github</span>. Si está en otra carpeta, GitHub no lo ve.</p></div>
  <div class="card"><h3>De dónde se copia</h3><p class="small"><b>Copiar el archivo</b> (arriba a la izquierda) copia el archivo completo, con sus comentarios. Es el mismo que <span class="mono">pruebas-proyecto.yml</span> de esta carpeta.</p></div>
  <div class="callout">No hay que entenderlo todo ya: las dos diapositivas siguientes lo leen línea a línea.</div>
 </div></div>''',
          'Este es todo el workflow. En pantalla se ve sin comentarios para que quepa; el botón copia el archivo completo, con comentarios que explican cada línea. Lea de arriba abajo en voz alta, sin detenerse: nombre, cuándo, permisos, el job y cuatro pasos. Después lo desmontamos.')

    slide('B', 4, 'Cuándo y con qué permisos', 'Anatomía · 1', '**Cuándo** se ejecuta y **qué puede** hacer', '''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="card">''' + tabla(['Línea', 'Qué hace'], [
        ['`name: Pruebas del proyecto`', 'el nombre que verás en la pestaña Actions'],
        ["`on: push: branches: ['lab/**']`", 'se dispara con cada `push` a una rama que empiece por `lab/`; `develop` y `main` **no**'],
        ['`workflow_dispatch:`', 'botón para lanzarlo a mano; GitHub solo lo muestra si el archivo está en la rama principal (hoy no lo usamos)'],
        ['`permissions: contents: read`', 'solo **leer** el repositorio: mínimo privilegio'],
        ['`runs-on: ubuntu-latest`', 'una máquina Linux nueva de GitHub'],
        ['`timeout-minutes: 10`', 'si algo se cuelga, se corta a los 10 minutos']]) + '''</div>
 <div class="col">
  <div class="card"><h3>No choca con los workflows del curso</h3>''' + tabla(['Workflow', 'Se dispara con'], [
        ['`validar-dos-contenedores.yml`', '`push` a `develop`'],
        ['`validar-codespace.yml`', '*pull requests*'],
        ['`validar-windows.yml`', 'cambios en `03-Entorno/`']]) + '''<p class="small" style="margin-top:8px">En la rama <span class="mono">lab/actions-s3</span> solo debería aparecer <b>Pruebas del proyecto</b>.</p></div>
  <div class="callout">El filtro de ramas es la decisión de diseño: probamos en una rama aparte sin tocar <span class="mono">develop</span>.</div>
 </div></div>''',
          'Primera mitad del archivo: cuándo y con qué permisos. El filtro lab/** hace que el laboratorio no se mezcle con nada: ni develop ni main lo disparan. Permisos: por defecto un workflow puede tener más permisos de los que necesita; aquí solo lee. El timeout evita que una prueba colgada consuma minutos durante horas. La tabla de la derecha es para quien se pregunte si van a saltar otros workflows del curso en su fork: no deberían, y en la pestaña Actions lo comprobamos.')

    slide('B', 4, 'Los cuatro pasos', 'Anatomía · 2', 'Los cuatro pasos del job', '''
<div class="grid2">
''' + ''.join(f'<div class="card"><h3>{md(t)}</h3><p class="small">{md(d)}</p></div>' for t, d in [
        ('1 · `uses: actions/checkout@v4`', 'Una **acción** ya hecha (código de otro, versionado con `@v4`): descarga tu repositorio en el runner, en el commit que acabas de subir.'),
        ('2 · `uses: actions/setup-python@v5`', 'Instala **Python 3.11**, el del curso. `cache: pip` guarda los paquetes descargados: el segundo run descarga menos.'),
        ('3 · `pip install -r requirements-dev.txt`', 'Las **mismas versiones** que el entorno del curso; luego `pip install -e . --no-deps` instala el paquete `ia_mlops`. `working-directory` hace que todo corra dentro de `04-Proyecto-Base`.'),
        ('4 · `python -m pytest -v …`', 'Las pruebas, con `-v` para ver una línea `PASSED` o `FAILED` por prueba. Si una falla, pytest termina con error, el paso se pone **en rojo** y el run también.')]) + '''
</div>
<div class="callout" style="margin-top:12px"><span class="mono">uses:</span> = usar una acción hecha · <span class="mono">run:</span> = ejecutar órdenes de terminal, igual que en tu Codespace.</div>''',
          'Segunda mitad: los pasos. Distinga uses de run: uses reutiliza una acción publicada por otros, con su versión; run son órdenes de bash normales, las mismas que escribirían en el Codespace. El paso 3 instala lo mismo que instala el workflow validar-dos-contenedores del curso. El paso 4 es el que decide el color.')

    slide('B', 3, 'Qué pruebas y por qué', 'Decisión · el subconjunto rápido', 'Tres archivos de pruebas, sin datos descargados', '''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="card">''' + tabla(['Archivo', 'Qué comprueba'], [
        ['`tests/test_raw_y_master.py`', 'la ingesta: capas RAW y MASTER'],
        ['`tests/test_fs_y_ml.py`', 'las variables (FS) y el conjunto del modelo (ML), por fecha de corte'],
        ['`tests/test_interfaz.py`', 'la interfaz de S2: ids → variables → modelo → recomendación, y la **regla de negocio** de tramos']]) + '''</div>
 <div class="col">
  <div class="card"><h3>Por qué estas</h3>''' + lista([
        '`tests/conftest.py` construye las bases desde la **muestra** del repositorio: no hay que descargar datos ni ejecutar antes el pipeline.',
        'No necesitan **Docker** ni ejecutar cuadernos (esas pruebas están marcadas `lento`).',
        'En `test_interfaz.py` está la prueba que vamos a romper.']) + '''</div>
  <div class="card"><h3>Cuánto tarda</h3><p class="small">En local (Windows): <span class="mono">test_raw_y_master</span> 6,8 s y <span class="mono">test_fs_y_ml</span> 4,5 s. En el Codespace (Linux): 45 pruebas en 21 s. En GitHub (20/11/2026): el run completo, <b>1 min 16 s</b> el primero y <b>51 s – 1 min 6 s</b> con la caché de pip; instalar dependencias es lo más largo (38–46 s) y las pruebas, 11–12 s.</p></div>
 </div></div>''',
          'Por qué no todas las pruebas: las de cuadernos son lentas y las de imagen y contenedores necesitan más; para aprender el ciclo verde, rojo, verde, conviene que el run sea corto. Las tres elegidas no necesitan datos: el conftest crea la base operacional y la analítica desde la muestra versionada. Los tiempos son los medidos en local; el del run en GitHub se completa con la captura.')

    # ---------------------------------------------------------------- C · Verde
    slide('C', 7, 'Preparar el fork y el Codespace', 'Antes de empezar', 'Tu fork, tu Codespace y Actions activado', '''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>1 · Fork</h3><p class="small">Si no tienes tu copia del repositorio del curso en tu cuenta, créala con <b>Fork</b>. El laboratorio se hace <b>en tu fork</b>: los runs corren en tu cuenta.</p></div>
  <div class="card"><h3>2 · Codespace</h3><p class="small">Ábrelo <b>desde tu fork</b>, en <span class="mono">develop</span>. Trabaja en la raíz: <span class="mono">/workspaces/&lt;tu-repositorio&gt;</span>.</p></div>
  <div class="card"><h3>3 · Actions en el fork</h3><p class="small">En los forks, GitHub puede tener Actions desactivado al principio. Entra en la pestaña <b>Actions</b>: <b>si ves un aviso</b> que pide activar los workflows, acéptalo. Si no hay aviso, nada que hacer.</p></div>
 </div>
 <div class="col">''' + term('Terminal del Codespace · en la raíz del repositorio', ['git switch develop', 'git pull', 'git status']) + mira([
        '`On branch develop` y nada pendiente.',
        'Si `git status` enseña cambios tuyos de otras sesiones, haz commit o guárdalos antes (`git stash`).']) + '''
 </div></div>''',
          'Dé tiempo: es donde más se atasca la gente. Comprobar tres cosas: que trabajan en su fork y no en el repositorio del curso (no tendrían permiso para subir), que el Codespace es de ese fork y que Actions está activado. El texto exacto del aviso de GitHub para activar Actions en un fork no lo afirmo aquí: que lo lean en su pantalla. Si alguien no tiene fork, que lo cree ahora y abra un Codespace nuevo.')

    slide('C', 6, 'Paso 1 · Rama y archivo', 'Pasos 1 y 2 · rama y workflow', 'Crea la rama y el archivo del workflow', f'''
<div class="split" style="grid-template-columns:.95fr 1.05fr">
 <div class="col">''' + term('Terminal del Codespace', [
        f'git switch -c {RAMA}',
        'mkdir -p .github/workflows',
        '# opción A: si tu fork tiene la carpeta del laboratorio',
        f'cp 01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-github-actions/pruebas-proyecto.yml .github/workflows/',
        '# opción B: abrirlo vacío, pegar con «Copiar el archivo» y guardar',
        f'code {DESTINO}',
        'git status']) + mira([
        f'`On branch {RAMA}` y `.github/` como **archivo nuevo sin seguimiento**.',
        'En el editor, la sangría de dos espacios tal cual. Nunca tabuladores.']) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['a01-rama.webp', 'a02-yaml.webp'])}{cap('a01-rama.webp', 220)}{cap('a02-yaml.webp', 220)}</div>
</div>''',
          'La rama primero: así develop no se toca. Dos formas de crear el archivo: copiarlo de la carpeta del laboratorio si el fork está al día, o abrirlo vacío con code y pegar el contenido con el botón Copiar el archivo de la diapositiva del workflow. Pida que miren la sangría en el editor. Si en la captura el archivo se creó de otra forma, explique que el resultado es el mismo archivo.')

    slide('C', 4, 'Paso 3 · Commit y push', 'Paso 3 · subir', 'Commit y push: aquí se dispara', f'''
<div class="split" style="grid-template-columns:.95fr 1.05fr">
 <div class="col">''' + term('Terminal del Codespace', [
        f'git add {DESTINO}',
        'git commit -m "Laboratorio S3: workflow que ejecuta las pruebas del proyecto"',
        f'git push -u origin {RAMA}']) + mira([
        'git crea la rama en GitHub; `-u` la deja enlazada: los próximos `git push` ya no llevan nombre.',
        'Si git pide nombre y correo: `git config user.name "Tu nombre"` y `git config user.email "tu-correo"`, y repite el commit.']) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['a03-push.webp'])}{cap('a03-push.webp', 400)}</div>
</div>''',
          'Este push es el disparador: la rama empieza por lab/, así que el filtro del workflow se cumple. Que nadie haga push a develop. Si alguien no tiene permiso para subir, casi seguro está en el repositorio del curso y no en su fork: git remote -v lo dice.')

    slide('C', 8, 'Paso 4 · Verde en Actions', 'Paso 4 · la pestaña Actions', 'El run en la pestaña Actions: en curso y en verde', f'''
{rotulo_capturas(['a04-actions-lista.webp', 'a05-run-curso.webp', 'a06-run-verde.webp'])}
<div class="grid3">{cap('a04-actions-lista.webp', 240)}{cap('a05-run-curso.webp', 240)}{cap('a06-run-verde.webp', 240)}</div>
<div class="grid3" style="margin-top:10px">
 {mira(['Un run de **Pruebas del proyecto** con el mensaje de tu commit y la rama `lab/actions-s3`; mientras corre, el círculo amarillo e «In progress».'], '1 · La lista')}
 {mira(['Entra en el run y en el job **pruebas**: los cuatro pasos, en orden, mientras se ejecutan.'], '2 · En curso')}
 {mira(['Todos los pasos en verde; en **Ejecutar las pruebas**, una línea `PASSED` por prueba y el resumen `passed`.'], '3 · Verde')}
</div>''',
          'Que abran la pestaña Actions de su fork en el navegador. El primer run tarda más porque descarga e instala los paquetes; la caché de pip ayuda en los siguientes. Mientras corre, abran el paso Ejecutar las pruebas y vean aparecer los PASSED. Si no aparece ningún run: archivo fuera de .github/workflows, rama que no empieza por lab/, o Actions sin activar en el fork. La duración real del run se añade cuando estén las capturas.')

    # ---------------------------------------------------------------- D · Rojo
    slide('D', 4, 'Paso 5 · Romper a propósito', 'Paso 5 · una línea', 'Romper la regla de negocio con **una línea**', f'''
<div class="split" style="grid-template-columns:.95fr 1.05fr">
 <div class="col">
  <div class="card"><h3>La regla</h3><p class="small">En <span class="mono">04-Proyecto-Base/ia_mlops/config.py</span>, <span class="mono">SEGMENTOS_RECOMPRA</span>: un cliente es <b>alta</b> desde una probabilidad de <b>0,70</b>. La subimos a 0,75 sin avisar a la prueba.</p></div>''' + term('Terminal del Codespace · en la raíz del repositorio', [
        ROTURA,
        'git diff',
        'git commit -am "Rotura a propósito: el tramo alta empieza en 0,75"',
        'git push']) + mira(["`git diff`: **una sola línea** cambiada, `'desde': 0.70` → `'desde': 0.75`."]) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['a07-rotura.webp'])}{cap('a07-rotura.webp', 400)}</div>
</div>''',
          'sed busca el texto desde 0.70 y lo cambia por 0.75 en el archivo; solo hay una aparición. Antes de mirar el resultado, pregunte: ¿qué prueba creen que fallará? Recoja hipótesis. Que todos miren el git diff antes del commit: es la costumbre de revisar lo que subes. Sin -u esta vez: la rama ya está enlazada.')

    slide('D', 3, 'Paso 6 · Rojo', 'Paso 6 · el run en rojo', 'El run nuevo sale en rojo', f'''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="capcol">{rotulo_capturas(['a08-run-rojo.webp'])}{cap('a08-run-rojo.webp', 420)}</div>
 <div class="col">{mira([
        'Un run nuevo con el mensaje «Rotura a propósito…», **en rojo**.',
        'Dentro, el paso **Ejecutar las pruebas** en rojo; los anteriores, en verde.',
        'El rojo no es un desastre: es el CI haciendo su trabajo **antes** de que llegue a nadie.'])}</div>
</div>''',
          'Señale que los pasos de descarga, Python e instalación siguen en verde: el problema no es del entorno, es del código. Tranquilice al grupo: el rojo es información, no un castigo. En un equipo, este rojo evita que el cambio llegue a develop.')

    slide('D', 8, 'Leer el registro', 'Paso 6 · leer el log', 'Leer el registro: **qué prueba**, **dónde** y **qué esperaba**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="realbox"><div class="rk">Salida real · la misma prueba en local · {FECHA}</div><pre>{esc(SALIDA_ROTA)}</pre></div>
  <div class="card"><h3>Cómo leerlo</h3>''' + lista([
        '`FAILED tests/test_interfaz.py::test_la_regla_de_negocio`: **qué prueba**.',
        'La prueba pide que **0,70** (segunda de la lista, **índice 1**) sea `alta`.',
        "`At index 1 diff: 'media' != 'alta'`: obtuvo `media`, esperaba `alta`.",
        'El resto sigue en `PASSED`: el fallo está **acotado**.']) + f'''</div>
 </div>
 <div class="capcol">{rotulo_capturas(['a09-log-error.webp'])}{cap('a09-log-error.webp', 440)}</div>
</div>''',
          'La diapositiva más importante del laboratorio. Lea el registro con el grupo de abajo arriba: primero el resumen short test summary info, luego las líneas E. La prueba está en tests/test_interfaz.py, línea 98: comprueba que 0,99 y 0,70 son alta, 0,69 y 0,40 media y 0,39 y 0 baja. Con el umbral en 0,75, el 0,70 cae en media. En GitHub, con -v, pytest muestra la lista completa. Pida que cada persona encuentre la línea en su propio registro.')

    slide('D', 3, '¿Prueba o código?', 'Paso 6 · decidir', '¿Está mal la prueba o está mal el cambio?', '''
<div class="grid2">
 <div class="card"><h3 class="okc">Arreglar el código</h3><p class="small">El umbral 0,70 es una <b>regla de negocio acordada</b> con quien hace la campaña. El cambio no estaba acordado: se deshace.</p></div>
 <div class="card"><h3 class="malc">No: borrar o retocar la prueba</h3><p class="small">Quitar la prueba pone el run en verde y <b>esconde</b> el problema. La prueba existe justo para proteger esa regla.</p></div>
</div>
<div class="callout" style="margin-top:14px">Si el negocio <b>decide</b> cambiar el umbral, se cambian <b>a la vez</b> la regla y la prueba, en el mismo commit, y el run verde lo deja documentado.</div>''',
          'Discusión corta. La tentación con un rojo es tocar la prueba hasta que pase. Aquí la respuesta es clara: el umbral es una decisión de negocio. Pero haga ver el caso contrario: si marketing decide 0,75, entonces se cambian regla y prueba juntas, y el CI demuestra que el cambio es coherente.')

    # ---------------------------------------------------------------- E · Arreglo y cierre
    slide('E', 4, 'Paso 7 · Arreglar', 'Paso 7 · git revert', 'Arreglar: deshacer el cambio con un commit nuevo', f'''
<div class="split" style="grid-template-columns:.95fr 1.05fr">
 <div class="col">''' + term('Terminal del Codespace', ['git revert --no-edit HEAD', 'git log --oneline -3', 'git push']) + mira([
        '`git revert` crea un commit **nuevo** («Revert …») que deshace el anterior.',
        '`git log`: los tres commits, el del workflow, la rotura y el revert. El historial **no se reescribe**.',
        "Otra forma: editar la línea a mano de vuelta a `0.70`, `git commit -am \"…\"` y `git push`."]) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['a10-arreglo.webp'])}{cap('a10-arreglo.webp', 400)}</div>
</div>''',
          'git revert es la forma segura de deshacer en una rama compartida: no borra la historia, añade un commit que la contrarresta. HEAD es el último commit, el de la rotura. --no-edit acepta el mensaje que propone git. Que miren git log: quedan los tres commits.')

    slide('E', 4, 'Paso 8 · Verde otra vez', 'Paso 8 · el historial', 'Verde otra vez, y el historial lo cuenta todo', f'''
{rotulo_capturas(['a11-run-verde-otra-vez.webp', 'a12-historial.webp'])}
<div class="grid2">{cap('a11-run-verde-otra-vez.webp', 300)}{cap('a12-historial.webp', 300)}</div>
<div class="grid2" style="margin-top:10px">
 {mira(['El run del revert, en verde: `test_la_regla_de_negocio` vuelve a `PASSED`.'], 'Verde')}
 {mira(['La lista de **Pruebas del proyecto**: **verde · rojo · verde**, con los tres mensajes de commit (#1, #2 y #3).'], 'Historial')}
</div>''',
          'Cierre del ciclo. La lista de runs es la evidencia: cada cambio se comprobó y se ve cuál rompió y cuál arregló. Esto es lo que pediremos en S4 como evidencia del workflow del caso propio: un historial de ejecuciones.')

    slide('E', 4, 'Si algo falla', 'Problemas típicos', 'Si algo falla', '<div class="card">' + tabla(['Síntoma', 'Causa probable', 'Qué hacer'], [
        ['No aparece ningún run', 'archivo fuera de `.github/workflows/`, rama sin `lab/` o Actions sin activar en el fork', '`git status`, `git branch --show-current`, pestaña Actions del fork'],
        ['El run falla sin llegar a los pasos', 'YAML mal sangrado (tabuladores, espacios de más)', 'abrir el archivo, comparar con el de la carpeta, volver a hacer push'],
        ['`git push` rechazado por permisos', 'el Codespace es del repositorio del curso, no de tu fork', '`git remote -v`; abrir un Codespace desde tu fork'],
        ['git pide nombre y correo', 'identidad sin configurar', '`git config user.name …` y `git config user.email …`'],
        ['Rojo en «Instalar dependencias»', 'fallo de red o de un paquete, no de tu código', 'leer la última línea del paso y relanzar el run'],
        ['`sed` no cambia nada', 'no estás en la raíz del repositorio', '`pwd`; ir a la raíz y repetir; `git diff` debe mostrar una línea']]) + '</div>',
          'Tenga esta diapositiva a mano durante los pasos 3 a 7. Los dos más frecuentes en un primer laboratorio: Actions sin activar en el fork y trabajar en el repositorio del curso en lugar del fork. El de instalar dependencias es raro, pero si pasa, que vean que el rojo está en otro paso: la causa es otra.')

    slide('E', 4, 'Limpieza y S4', 'Al terminar · y lo que viene', 'Limpieza, y el puente a S4', '''
<div class="split" style="grid-template-columns:.9fr 1.1fr">
 <div class="col">''' + term('Limpieza · cuando ya no necesites la rama', ['git switch develop', f'git push origin --delete {RAMA}', f'git branch -D {RAMA}']) + '''
  <p class="small">Los runs ya ejecutados se quedan en Actions como historial.</p></div>
 <div class="card"><h3>En S4, el workflow hará más</h3>''' + lista([
        'El **pipeline** raw → modelo y el registro en **MLflow**.',
        '**Construir y publicar la imagen** en Artifact Registry (Google Cloud).',
        '**Desplegar en Cloud Run con aprobación**: un paso que espera a que una persona autorizada lo apruebe.',
        '**Autenticación sin claves**: *Workload Identity Federation*. GitHub demuestra quién es con un token de corta duración y Google le da solo los permisos necesarios. Ninguna clave en el repositorio.',
        'Paso intermedio ya escrito: `04-Proyecto-Base/deploy/github-actions/ci.yml` (pruebas + construir y probar la imagen).']) + '''</div>
</div>''',
          'La limpieza es opcional: la rama no molesta, pero conviene acostumbrarse a borrar ramas de prueba. Puente a S4: el mismo mecanismo, con más pasos. Lo que más interesa adelantar es la autenticación sin claves: nunca se guarda una clave de servicio de GCP en GitHub; se usa Workload Identity Federation. La plantilla ci.yml del proyecto ya hace pruebas más imagen.')

    slide('E', 3, 'Autoevaluación y cierre', 'Comprueba que lo tienes', 'Cinco preguntas', '<div class="grid2">' + ''.join(
        f'<div class="card"><h3>{i}. {md(p)}</h3><p class="small">{md(r)}</p></div>' for i, (p, r) in enumerate([
            ('¿Qué líneas deciden **cuándo** se ejecuta?', "`on: push: branches: ['lab/**']` (y `workflow_dispatch` para lanzarlo a mano)."),
            ('¿Por qué `permissions: contents: read`?', 'Mínimo privilegio: el workflow no necesita escribir nada.'),
            ('¿Por qué sale verde sin tu entorno conda?', 'Porque instala todo desde `requirements-dev.txt` en una máquina limpia: justo lo que comprueba.'),
            ('El run sale rojo: ¿dónde miras primero?', 'En el paso rojo: la línea `FAILED` y las líneas `E` de debajo.'),
            ('¿Por qué no se arregla borrando la prueba?', 'Porque protege una regla acordada: borrarla esconde el problema.')], 1)) + '</div>',
          'Lea cada pregunta y deje que respondan antes de leer la respuesta. Cierre con la idea del día: cada cambio se comprueba solo, en una máquina limpia, y un rojo bien leído dice qué cambio rompió qué. En S4, el mismo workflow construye, publica y despliega.')


# =====================================================================================================================================
# Marco: CSS (fondo blanco, sin movimiento al pasar el ratón) y JavaScript del visor
# =====================================================================================================================================
CSS = r"""
:root{--tinta:#1f2937;--suave:#5b6472;--linea:#d6dde6;--fondo:#ffffff;--gris:#f4f6f9;--acento:#0b5cad;--ok:#15803d;--mal:#b91c1c;--aviso:#92400e;
 --mono:Consolas,"Cascadia Mono","DejaVu Sans Mono",Menlo,monospace;--sans:"Segoe UI",system-ui,-apple-system,Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#e8ecf1;color:var(--tinta);font-family:var(--sans)}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}
#viewport{position:fixed;inset:0 0 48px 0;display:flex;align-items:center;justify-content:center;overflow:hidden}
#stage{width:1280px;height:720px;flex:none;position:relative;transform:scale(var(--s,1));background:var(--fondo);box-shadow:0 2px 14px rgba(0,0,0,.12)}
.slide{position:absolute;inset:0;padding:34px 52px 46px;display:none;flex-direction:column;gap:12px;overflow:hidden}
.slide.active{display:flex}
.kick{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--acento);font-weight:700}
h1{font-size:34px;line-height:1.15;font-weight:700;margin-bottom:6px}
h3{font-size:18px;margin-bottom:6px}
.sub{font-size:22px;line-height:1.4;color:var(--suave);max-width:1050px}
.cover{display:flex;flex-direction:column;justify-content:center;flex:1}
.chips{display:flex;gap:8px;margin-top:18px;flex-wrap:wrap}
.tag{display:inline-block;font-size:13px;padding:3px 10px;border-radius:999px;border:1px solid var(--linea);background:var(--gris);color:var(--tinta)}
.tag.ok{border-color:#86c79c;background:#ecf8f0;color:var(--ok)}.tag.warn{border-color:#e2b56b;background:#fdf6e9;color:var(--aviso)}
.card{border:1px solid var(--linea);border-radius:12px;padding:12px 16px;background:#fff}
.callout{border-left:4px solid var(--acento);background:#eef5fc;padding:10px 14px;border-radius:0 10px 10px 0;font-size:17px;line-height:1.4}
.small{font-size:15.5px;line-height:1.45}
.mono{font-family:var(--mono);font-size:.92em;background:var(--gris);padding:0 4px;border-radius:4px}
.okc{color:var(--ok)}.malc{color:var(--mal)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.split{display:grid;gap:18px;min-height:0}.col,.capcol{display:flex;flex-direction:column;gap:10px;min-width:0}
.list{list-style:none;display:flex;flex-direction:column;gap:5px}.list li{font-size:15.5px;line-height:1.4;padding-left:16px;position:relative}
.list li::before{content:"";position:absolute;left:2px;top:8px;width:6px;height:6px;border-radius:50%;background:var(--acento)}
.ol{padding-left:24px;display:flex;flex-direction:column;gap:6px;font-size:17px}
.mira h3{color:var(--acento);font-size:16px}.mira .list li{font-size:14.5px}
.tbl{width:100%;border-collapse:collapse;font-size:14.5px}.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--suave);border-bottom:2px solid var(--linea);padding:5px 8px}
.tbl td{border-bottom:1px solid var(--linea);padding:6px 8px;line-height:1.35;vertical-align:top}
.term{border:1px solid var(--linea);border-radius:10px;background:var(--gris);overflow:hidden}
.term .bar{display:flex;align-items:center;gap:8px;padding:5px 10px;border-bottom:1px solid var(--linea);background:#eaeef3}
.term .bar em{flex:1;font-style:normal;font-size:12.5px;color:var(--suave)}
.tls{padding:6px 8px;font-family:var(--mono);font-size:13.5px;line-height:1.45}
.tln{display:flex;align-items:flex-start;gap:6px;padding:2px 4px}
.tln code{flex:1;white-space:pre-wrap;overflow-wrap:anywhere;font-family:var(--mono)}
.tln.c{color:var(--suave);font-style:italic}
.ps{color:var(--ok);font-weight:700}
.cp{flex:none;min-width:26px;height:24px;border-radius:6px;border:1px solid #b9c3cf;background:#fff;font-size:13px;color:var(--suave)}
.cp.ok{border-color:var(--ok);color:var(--ok)}.cpall{padding:0 10px;font-size:12px;font-family:var(--sans)}
.yml2{display:grid;grid-template-columns:.8fr 1.2fr}
.yml{font-family:var(--mono);font-size:13.5px;line-height:1.42;padding:10px 12px;overflow:hidden}
.yl{display:block;white-space:normal;overflow-wrap:anywhere}
.yml+.yml{border-left:1px solid var(--linea)}
.realbox{border:1px solid #86c79c;background:#f3fbf5;border-radius:10px;padding:8px 12px}
.realbox .rk{font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--ok);font-weight:700;margin-bottom:3px}
.realbox pre{font-family:var(--mono);font-size:13px;line-height:1.4;white-space:pre-wrap;overflow-wrap:anywhere}
.rot{margin:-6px 0 0}
.cap{display:flex;flex-direction:column;gap:4px;min-width:0}
.cap figcaption{font-size:12.5px;color:var(--suave)}
.zoom{display:block;position:relative;cursor:zoom-in;text-align:left}
.zoom img{display:block;max-width:100%;height:auto;border:1px solid var(--linea);border-radius:8px}
.lupa{position:absolute;right:6px;bottom:6px;font-size:11.5px;background:rgba(255,255,255,.92);border:1px solid var(--linea);border-radius:6px;padding:1px 6px;display:flex;align-items:center;gap:4px;color:var(--suave)}
.pend{border:2px dashed #c9a65e;background:#fdf9f0;border-radius:10px;min-height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:10px;text-align:center;font-size:13.5px;color:var(--aviso)}
.pend b{font-size:16px}
svg .nodo{fill:#f4f8fc;stroke:#8fb2d6;stroke-width:1.5}svg .nodo.job{fill:#fff}svg .nodo.ok{fill:#ecf8f0;stroke:var(--ok)}svg .nodo.mal{fill:#fdeeee;stroke:var(--mal)}
svg .paso{fill:var(--gris);stroke:var(--linea)}svg .fl{stroke:var(--acento);stroke-width:2;fill:none}
svg .t1{font:700 15px var(--sans);fill:var(--tinta);text-anchor:middle}svg .t2{font:13px var(--sans);fill:var(--suave);text-anchor:middle}
svg .tok{fill:var(--ok)}svg .tmal{fill:var(--mal)}
.card svg{display:block;width:100%;height:auto}
.foot{position:absolute;left:52px;right:52px;bottom:14px;display:flex;justify-content:space-between;font-size:12px;color:var(--suave);border-top:1px solid var(--linea);padding-top:6px}
#prog{position:fixed;left:0;top:0;height:3px;background:var(--acento);z-index:5}
#bar{position:fixed;left:0;right:0;bottom:0;height:48px;display:flex;align-items:center;gap:6px;padding:0 12px;background:#fff;border-top:1px solid var(--linea);font-size:13px;z-index:6}
#bar button,#bar a{border:1px solid var(--linea);border-radius:8px;padding:4px 10px;background:#fff;color:var(--tinta);text-decoration:none;font-size:13px}
#bar .part.on{border-color:var(--acento);color:var(--acento);font-weight:700}
#bar .sp{flex:1}#count,#clockref{color:var(--suave);padding:0 6px}
#notes{position:fixed;right:0;top:0;bottom:48px;width:400px;background:#fff;border-left:1px solid var(--linea);padding:18px;overflow:auto;display:none;z-index:7;font-size:15px;line-height:1.5}
#notes.on{display:block}#notes h3{margin-bottom:8px}
#index{position:fixed;inset:0 0 48px 0;background:rgba(255,255,255,.98);display:none;z-index:8;padding:28px;overflow:auto}
#index.on{display:block}#index .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
#index button{border:1px solid var(--linea);border-radius:10px;padding:10px;text-align:left;font-size:14px;background:#fff}
#index button small{display:block;color:var(--suave);font-size:12px}#index button.cur{border-color:var(--acento)}
#zoombox{position:fixed;inset:0;background:rgba(20,26,34,.86);display:none;z-index:9;align-items:center;justify-content:center;padding:24px;cursor:zoom-out}
#zoombox.on{display:flex}#zoombox img{max-width:100%;max-height:100%;background:#fff;border-radius:6px}
#zoombox p{position:fixed;top:10px;left:0;right:0;text-align:center;color:#fff;font-size:13px}
@media print{#bar,#notes,#index,#prog,.cp{display:none!important}}
"""

JS = r"""
(function(){
'use strict';
const $=(s,r)=>(r||document).querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PARTES=__PARTES__;
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){try{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();return true}catch(e2){return false}}}
const slides=$$('.slide'), N=slides.length; let cur=0;
slides.forEach((s,i)=>{const f=document.createElement('div');f.className='foot';
  f.innerHTML=`<span>ML e IA · S3 · Laboratorio de GitHub Actions</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
function go(i){i=Math.max(0,Math.min(N-1,i));cur=i;slides.forEach((s,k)=>s.classList.toggle('active',k===i));chrome();try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function chrome(){const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N; $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL;
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML='<p>'+esc(s.dataset.notes||'')+'</p>';
  $('#notemin').textContent='Tiempo previsto: '+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' min de '+TOTAL;
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur));}
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(PARTES[s.dataset.part]||'')} · ${s.dataset.min||0} min</small>${i+1}. ${esc(s.dataset.title||'')}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;toggle('#index',false);go(+b.dataset.i)});
function toggle(sel,force){$(sel).classList.toggle('on',force)}
$('#bprev').onclick=()=>go(cur-1); $('#bnext').onclick=()=>go(cur+1);
$('#bidx').onclick=()=>toggle('#index'); $('#bnotes').onclick=()=>toggle('#notes');
$('#bfull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()};
$$('#bar .part').forEach(b=>b.onclick=()=>go(slides.findIndex(s=>s.dataset.part===b.dataset.p)));
function zoom(on,src,alt){const z=$('#zoombox');if(on){$('#zoomimg').src=src;$('#zoomimg').alt=alt||'';}z.classList.toggle('on',!!on)}
$('#zoombox').onclick=()=>zoom(false);
addEventListener('keydown',e=>{
  const t=e.target; if(t&&/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  if(e.ctrlKey||e.metaKey||e.altKey) return;
  const k=e.key;
  if(k==='Escape'){zoom(false);toggle('#index',false);toggle('#notes',false);return}
  if($('#zoombox').classList.contains('on')) return;
  if(k==='ArrowRight'||k==='PageDown'||(k===' '&&!/^(BUTTON|A)$/.test(t.tagName))){e.preventDefault();go(cur+1)}
  else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();go(cur-1)}
  else if(k==='Home'){e.preventDefault();go(0)} else if(k==='End'){e.preventDefault();go(N-1)}
  else if(k==='o'||k==='O'){toggle('#index')} else if(k==='s'||k==='S'){toggle('#notes')} else if(k==='f'||k==='F'){$('#bfull').click()}
});
let tx=null;
addEventListener('touchstart',e=>{tx=e.touches[0].clientX},{passive:true});
addEventListener('touchend',e=>{if(tx===null)return;const dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>60){dx<0?go(cur+1):go(cur-1)}},{passive:true});
document.addEventListener('click',async e=>{
  const z=e.target.closest('.zoom'); if(z){e.stopPropagation();zoom(true,z.dataset.src,z.dataset.alt);return}
  const b=e.target.closest('.cp'); if(!b) return; e.stopPropagation();
  const ok=await copyText(b.dataset.t); const t=b.textContent; b.classList.add('ok'); b.textContent=ok?'✓':'✗'; setTimeout(()=>{b.classList.remove('ok');b.textContent=t},1200)});
fit();
const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
addEventListener('hashchange',()=>{const n=parseInt((location.hash||'').slice(1),10);if(!isNaN(n)&&n-1!==cur)go(n-1)});
})();
"""


def html_completo():
    import json
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Laboratorio de GitHub Actions · S3 · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S3">⌂ S3</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en guia.md, en esta carpeta.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    pendientes = [n for n in CAPTURAS if not (AQUI / 'img' / n).is_file()]
    if a.comprobar:
        if actual != nuevo:
            print('DESFASADO: ejecuta python generar.py')
            sys.exit(1)
        print('al día')
        return
    if actual == nuevo:
        print('sin cambios')
    else:
        SALIDA.write_text(nuevo, encoding='utf-8')
        minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
        print(f'escrito {SALIDA.name}: {len(SLIDES)} diapositivas, {minutos} min')
    if pendientes:
        print(f'capturas pendientes ({len(pendientes)}): ' + ', '.join(pendientes))


if __name__ == '__main__':
    main()
