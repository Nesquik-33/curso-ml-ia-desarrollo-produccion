"""Genera la presentación «Laboratorio de red neuronal» (index.html, junto a este archivo).

Bloque de S3 de 30 minutos: qué es una red neuronal y una CNN, transferencia (MobileNetV3-small congelada + regresión
logística), los datos (Oxford-IIIT Pet, CC BY-SA 4.0) y, en el Codespace, instalar, preparar las fotos, entrenar, verlo en
MLflow y predecir una foto con red_gato_perro.py. El mismo recorrido, en texto, está en guia.md.

Marco: el de laboratorio-mlflow (botón ⧉ para copiar cada orden, teclas ← → · O índice · S notas · F pantalla completa,
reloj de minutos planificados, «⌂ S3»), con fondo blanco y sin efectos al pasar el ratón. Las capturas se amplían con un clic.

Capturas: img/n01-instalar.webp … img/n05-predecir.webp (CAPTURAS). Si falta alguna, sale «Captura pendiente».

Salidas: REALES, de la ejecución en local (Windows, Python 3.11.18, torch 2.15.0+cpu, MLflow 3.18.0, 20/11/2026) de las mismas
órdenes. Cifras del estudio previo: 00-Planificacion/s3/_pico_red_neuronal/INFORME.md.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
IMG = AQUI / 'img'
FECHA = '20/11/2026'
LOCAL = f'Salida real · ejecución en local · {FECHA}'
INICIO_SESION = 0
DURACION = 30

CAPTURAS = {
    'n01-instalar.webp': 'Codespace del curso: instalar torch y torchvision (CPU) en 1 min 21 s',
    'n02-datos.webp': 'Codespace del curso: red_gato_perro.py datos',
    'n03-entrenar.webp': 'Salida real en local (Windows): red_gato_perro.py entrenar',
    'n04-mlflow.webp': 'MLflow en local: experimento gato-perro con sus dos runs',
    'n05-predecir.webp': 'Salida real en local (Windows): red_gato_perro.py predecir',
}

RAIZ_CS = '/workspaces/curso-ml-ia-desarrollo-produccion/04-Proyecto-Base'
O = {
    'ir': f'cd {RAIZ_CS}',
    'activar': 'conda activate env-ia-mlops',
    'instalar': 'pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu',
    'lab': 'LAB=../01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-red-neuronal',
    'datos': 'python $LAB/red_gato_perro.py datos',
    'datos100': 'python $LAB/red_gato_perro.py datos --por-clase 100',
    'entrenar': 'python $LAB/red_gato_perro.py entrenar',
    'ui': 'python -m ia_mlops.mlflow_ui',
    'perro': 'python $LAB/red_gato_perro.py predecir ~/datos-mascotas/fotos/perro/yorkshire_terrier_166.png',
    'gato': 'python $LAB/red_gato_perro.py predecir ~/datos-mascotas/fotos/gato/Abyssinian_142.png',
}
UI_PLAN_B = ('python -m mlflow ui --backend-store-uri "$(python -c \'from ia_mlops import mlflow_ui; print(mlflow_ui.uri())\')" '
             '--port 5000')

SALIDAS = {
    'datos': ('Descargando https://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz (unos 792 MB) ...\n'
              '   10 %  (80 MB, 13 s)\n'
              '  ...\n'
              '  100 %  (792 MB, 99 s)\n'
              'En el archivo: 2400 fotos de gato y 4990 de perro. Se usan 300 de cada clase.\n'
              'Fotos de 128×128 guardadas en …/datos-mascotas/fotos  (8 s)\n'
              'parte   gato  perro\n'
              'train    210    210\n'
              'val       45     45\n'
              'test      45     45'),
    'entrenar': ('Fotos: train 420 · val 90 · test 90\n'
                 'MobileNetV3-small cargada y congelada: 927.008 parámetros que NO se entrenan\n'
                 'Rasgos extraídos: 576 por foto en 0.4 s\n'
                 '  C=0.01   exactitud en val = 0.878  pérdida logarítmica en val = 0.300\n'
                 '  C=0.1    exactitud en val = 0.878  pérdida logarítmica en val = 0.247\n'
                 '  C=1.0    exactitud en val = 0.878  pérdida logarítmica en val = 0.302\n'
                 '  C=10.0   exactitud en val = 0.878  pérdida logarítmica en val = 0.429\n'
                 'Cabeza entrenada en 0.1 s · C elegida = 0.1\n'
                 'Exactitud en val = 0.878 · en test = 0.933  (6 fallos de 90)\n'
                 'Tiempo total (con registrar en MLflow): 5.8 s\n'
                 'Registrado en MLflow como «gato-perro», versión 3'),
    'perro': ('Modelo «gato-perro» versión 3 · foto yorkshire_terrier_166.png\n'
              'gato 0,04 / perro 0,96\n'
              'Predicción: perro'),
    'gato': ('Modelo «gato-perro» versión 3 · foto Abyssinian_142.png\n'
             'gato 0,55 / perro 0,45\n'
             'Predicción: gato'),
}


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)


def term(titulo, claves):
    filas, todo = [], []
    for k in claves:
        if k.startswith('#'):
            filas.append(f'<div class="tln c">{esc(k)}</div>')
            continue
        orden = O[k]
        todo.append(orden)
        filas.append(f'<div class="tln"><span class="ps">$</span><code>{esc(orden)}</code>'
                     f'<button class="cp" data-t="{esc(orden)}" title="Copiar" aria-label="Copiar la orden">⧉</button></div>')
    boton = (f'<button class="cp cpall" data-t="{esc(chr(10).join(todo))}">⧉ Copiar todo</button>' if len(todo) > 1 else '')
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em>{boton}</div>'
            f'<div class="tls">{"".join(filas)}</div></div>')


def real(clave, fuente=LOCAL, pq=False):
    return f'<div class="realbox{" pq" if pq else ""}"><div class="rk">{esc(fuente)}</div><pre>{esc(SALIDAS[clave])}</pre></div>'


def cap(nombre, alto=None):
    if nombre not in CAPTURAS:
        raise KeyError(f'captura no prevista: {nombre}')
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    if (IMG / nombre).exists():
        return (f'<figure class="cap"><button class="capa" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Clic para ampliar">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}></button><figcaption>{esc(alt)}</figcaption></figure>')
    alto_falta = f' style="min-height:{min(alto, 200)}px"' if alto else ''
    return (f'<figure class="cap"><div class="falta" data-falta="{nombre}"{alto_falta}><b>Captura pendiente</b>'
            f'<span class="mono">img/{nombre}</span><small>{esc(alt)}</small></div><figcaption>{esc(alt)}</figcaption></figure>')


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def mira(items):
    return '<div class="card mira"><h3>Qué debes ver</h3>' + lista(items) + '</div>'


def falla(items):
    return '<div class="card falla"><h3>Si falla</h3>' + lista(items) + '</div>'


def hazlo(items):
    return '<div class="card"><h3>Haz esto</h3>' + lista(items) + '</div>'


def tabla(cab, filas):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


PARTES = {'A': 'La idea', 'B': 'Los datos', 'C': 'Práctica', 'D': 'Cierre'}
SLIDES = []


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    SLIDES.append(dict(parte=parte, min=minutos, titulo=titulo, notas=notas,
                       html=f'<p class="kick">{esc(kick)}</p><h1>{md(h1)}</h1>\n{cuerpo}'))


def svg_red():
    """Una neurona y una CNN muy simplificadas: píxeles → filtros → rasgos → decisión."""
    o = ['<defs><marker id="fr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0 L10 5 L0 10 z" fill="#1f5fa8"/></marker></defs>']
    # neurona
    for i, y in enumerate((30, 75, 120)):
        o.append(f'<circle cx="30" cy="{y}" r="13" class="sv-n"/><text x="30" y="{y + 5}" class="sv-s">x{i + 1}</text>'
                 f'<path d="M43 {y} L147 75" stroke="#9fb3c8" stroke-width="2"/>'
                 f'<text x="92" y="{(y + 75) / 2 - 4}" class="sv-s">w{i + 1}</text>')
    o.append('<circle cx="170" cy="75" r="24" class="sv-g"/><text x="170" y="80" class="sv-t">Σ</text>'
             '<path d="M194 75 L250 75" stroke="#1f5fa8" stroke-width="2.5" marker-end="url(#fr)"/>'
             '<text x="275" y="80" class="sv-s">salida</text>'
             '<text x="150" y="170" class="sv-s">Una neurona: suma ponderada + función (w = pesos que se aprenden)</text>')
    # CNN
    x0 = 360
    pasos = [('Foto', '128×128×3 píxeles', 'n'), ('Filtros', 'bordes, texturas', 'n'), ('Filtros', 'ojos, orejas, pelo', 'n'),
             ('Rasgos', '576 números', 'g'), ('Cabeza', 'P(gato), P(perro)', 'g')]
    for i, (t, s, c) in enumerate(pasos):
        x = x0 + i * 156
        o.append(f'<rect x="{x}" y="35" width="136" height="80" rx="12" class="sv-{c}"/>'
                 f'<text x="{x + 68}" y="68" class="sv-t">{esc(t)}</text><text x="{x + 68}" y="92" class="sv-s">{esc(s)}</text>')
        if i:
            o.append(f'<path d="M{x - 20} 75 L{x - 3} 75" stroke="#1f5fa8" stroke-width="2.5" marker-end="url(#fr)"/>')
    o.append(f'<text x="{x0 + 380}" y="170" class="sv-s">Una CNN (red convolucional): capas de filtros que miran trozos de la imagen</text>')
    return f'<svg viewBox="0 0 1140 190" role="img" aria-label="Una neurona y una red convolucional">{"".join(o)}</svg>'


def svg_transferencia():
    o = ['<defs><marker id="ft" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0 L10 5 L0 10 z" fill="#1f5fa8"/></marker></defs>']
    o.append('<rect x="10" y="40" width="160" height="90" rx="12" class="sv-n"/><text x="90" y="80" class="sv-t">Foto</text>'
             '<text x="90" y="104" class="sv-s">128×128</text>'
             '<rect x="230" y="20" width="420" height="130" rx="12" class="sv-n" stroke-dasharray="6 4"/>'
             '<text x="440" y="70" class="sv-t">MobileNetV3-small (ImageNet)</text>'
             '<text x="440" y="96" class="sv-s">927 008 parámetros · CONGELADA: no se tocan</text>'
             '<text x="440" y="120" class="sv-s">ya sabe ver bordes, texturas, formas</text>'
             '<rect x="710" y="40" width="150" height="90" rx="12" class="sv-n"/><text x="785" y="80" class="sv-t">576 rasgos</text>'
             '<text x="785" y="104" class="sv-s">por foto</text>'
             '<rect x="920" y="30" width="210" height="110" rx="12" class="sv-g"/><text x="1025" y="70" class="sv-t">Cabeza</text>'
             '<text x="1025" y="94" class="sv-s">regresión logística</text><text x="1025" y="116" class="sv-s">577 pesos: SE ENTRENA</text>')
    for a, b in ((170, 226), (650, 706), (860, 916)):
        o.append(f'<path d="M{a} 85 L{b} 85" stroke="#1f5fa8" stroke-width="2.5" marker-end="url(#ft)"/>')
    return f'<svg viewBox="0 0 1140 160" role="img" aria-label="Transferencia: red congelada y cabeza entrenada">{"".join(o)}</svg>'


# =====================================================================================================================================
def construir():
    SLIDES.clear()

    slide('A', 2, 'Portada', 'S3 · Laboratorio de red neuronal', '¿Perro o gato? Una **red neuronal** en 30 minutos', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  <p class="sub">En tu Codespace: descargas fotos reales, usas una red ya entrenada con millones de imágenes, le pones una «cabeza» propia, la registras en MLflow con su firma y predices una foto.</p>
  <div class="card"><h3>Cómo seguirla</h3>{lista([
        'Cada orden lleva **⧉**: cópiala y pégala en el terminal del Codespace.',
        f'Las salidas son **reales** (ejecución en local, {FECHA}); en tu Codespace los tiempos y la versión pueden cambiar.',
        'El mismo recorrido en texto: `laboratorio-red-neuronal/guia.md`.',
        'Teclas: **← →** avanzar · **O** índice · **S** notas · **F** pantalla completa.'])}</div>
 </div>
 <div class="card"><h3>Palabras de hoy</h3>{tabla(['Palabra', 'Qué es'], [
        ['**Neurona**', 'Suma ponderada de entradas + una función. Los pesos se aprenden.'],
        ['**CNN**', 'Red convolucional: capas de filtros que recorren la imagen.'],
        ['**Rasgos**', 'Los números que la red saca de una foto: aquí, 576.'],
        ['**Transferencia**', 'Reutilizar una red ya entrenada para otra tarea.'],
        ['**Cabeza**', 'La última parte, la única que entrenamos hoy.']])}</div>
</div>''',
          'Bienvenida. Es un laboratorio corto: el objetivo no es dominar redes neuronales, sino ver que el ciclo del curso (datos, entrenar, registrar en MLflow con firma, predecir) es el mismo con imágenes. Recuerde que la guía en texto permite seguir solo a quien se quede atrás.')

    slide('A', 3, 'Red neuronal y CNN', 'A · La idea', 'De una **neurona** a una **red convolucional**', f'''
<div class="card" style="padding:12px 16px">{svg_red()}</div>
<div class="grid3" style="margin-top:14px">
 <div class="card"><h3>Neurona</h3><p class="small">Multiplica cada entrada por un peso, suma y aplica una función. La regresión logística de S1 es, de hecho, <b>una sola neurona</b>.</p></div>
 <div class="card"><h3>Red</h3><p class="small">Muchas neuronas en capas. Entrenar = ajustar los pesos para equivocarse menos, con muchos ejemplos.</p></div>
 <div class="card"><h3>Convolucional</h3><p class="small">Para imágenes: pequeños filtros recorren la foto. Las primeras capas ven bordes; las últimas, partes como orejas u ojos.</p></div>
</div>''',
          'Una sola idea: una neurona es una suma ponderada con una función, y la regresión logística que ya conocen es una neurona. Una CNN apila capas de filtros; lo que sale al final es un resumen numérico de la foto, los rasgos. No entre en retropropagación ni en fórmulas.')

    slide('A', 3, 'Transferencia', 'A · El truco de hoy', 'Transferencia: red **congelada** + **cabeza** nueva', f'''
<div class="card" style="padding:12px 16px">{svg_transferencia()}</div>
<div class="split" style="grid-template-columns:1fr 1fr;margin-top:12px">
 <div class="card"><h3>Por qué así</h3>{lista([
        'Entrenar una CNN desde cero en CPU: **566 s** y **86,4 %** (con CIFAR-10, estudio previo).',
        'Con MobileNet congelada + cabeza a 128×128: **93,1 %** en test (720 fotos) y la cabeza se entrena en segundos (estudio previo).',
        'Los pesos de MobileNetV3-small ocupan **10,3 MB** y se descargan una vez.'])}</div>
 <div class="card falla"><h3>Ojo: no es magia</h3>{lista([
        'ImageNet, con el que se entrenó MobileNet, **ya contiene perros y gatos**: la red ya «sabe» bastante de ellos.',
        'Por eso funciona tan bien con tan pocos datos: es **transferencia**, no una red que aprenda de cero.'])}</div>
</div>''',
          'Fuente de las cifras: 00-Planificacion/s3/_pico_red_neuronal/INFORME.md (tiempos en un portátil limitado a 2 procesadores lógicos; referencia, no promesa). Insista en la honestidad: ImageNet ya tiene razas de perros y gatos, así que la tarea es fácil para esta red. Lo importante es el patrón: reutilizar una red grande y entrenar solo la cabeza.')

    slide('B', 2, 'Los datos', 'B · Los datos', 'Oxford-IIIT Pet: fotos **reales** de gatos y perros', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="card"><h3>El conjunto</h3>{lista([
        'Archivo `images.tar.gz`: **791,9 MB**; dentro, **2 400** fotos de gato y **4 990** de perro (contadas por el script).',
        'La etiqueta va en el nombre del fichero: inicial **mayúscula = gato** (`Abyssinian_142.jpg`), minúscula = perro (`yorkshire_terrier_166.jpg`).',
        'Usamos **300 por clase** (equilibrado), elegidas con semilla 42; reparto **70/15/15** train/val/test.',
        'Cada foto: recorte centrado a cuadrado y reducción a **128×128** (el mismo paso al predecir).'])}</div>
 <div class="card"><h3>Licencia y cita</h3>{lista([
        '**CC BY-SA 4.0**, según la página oficial de VGG (Universidad de Oxford). Los derechos de cada foto siguen en sus autores.',
        'Si redistribuyes fotos o derivados: **cita** y **comparte igual**.',
        'Cita: Parkhi, Vedaldi, Zisserman, Jawahar, «Cats and Dogs», CVPR 2012.',
        'Las fotos se quedan en `~/datos-mascotas/`, **fuera del repositorio**.'])}</div>
</div>''',
          'Los conteos 2 400 y 4 990 los imprime el propio script; el tamaño del archivo está en el INFORME. Subraye que la etiqueta sale del nombre del fichero, una convención documentada del conjunto, y que no subimos fotos al repositorio: por licencia y por tamaño.')

    slide('C', 3, 'Instalar', 'C · Paso 1 · terminal', 'Instalar **PyTorch** (solo CPU) en el entorno del curso', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('Terminal del Codespace', ['ir', 'activar', 'instalar'])}
  {mira(['En el Codespace del curso tardó **1 min 21 s** y dejó `torch 2.15.0+cpu` y `torchvision 0.29.2+cpu`.',
         '`mlflow`, `scikit-learn` y `pillow` ya están en `env-ia-mlops`.'])}
  {falla(['Sin `--index-url …/whl/cpu`, pip baja la versión con GPU: muchos más MB y no la usamos.'])}
 </div>
 <div class="col capcol">{cap('n01-instalar.webp', 330)}</div>
</div>''',
          'El índice de PyTorch para CPU evita descargar las librerías de GPU. Mientras instala, explique qué es torchvision: modelos y utilidades de imagen, entre ellos MobileNetV3-small con sus pesos de ImageNet. Las versiones exactas están en requisitos.txt.')

    slide('C', 3, 'Preparar las fotos', 'C · Paso 2 · terminal', '`datos`: descargar, elegir y reducir a **128×128**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('Terminal del Codespace (en 04-Proyecto-Base)', ['lab', 'datos'])}
  {real('datos', pq=True)}
 </div>
 <div class="col capcol">{cap('n02-datos.webp', 260)}
  {falla(['Va lento: `datos --por-clase 100` (200 fotos) sirve para seguir.',
          'Si `~/datos-mascotas/images.tar.gz` ya existe, no se vuelve a descargar.'])}</div>
</div>''',
          'La descarga en el Codespace fue de unos 9 segundos; en local, por el proxy, 99 s. El script lee el archivo dos veces: primero los nombres, para elegir con semilla sin cargar 792 MB en memoria, y después solo las fotos elegidas. Deja reparto.csv con la parte de cada foto.')

    slide('C', 4, 'Entrenar la cabeza', 'C · Paso 3 · terminal', '`entrenar`: rasgos de MobileNet + **regresión logística**', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  {term('Terminal del Codespace', ['entrenar'])}
  {real('entrenar', pq=True)}
 </div>
 <div class="col capcol">{cap('n03-entrenar.webp', 250)}
  {mira(['**927 008** parámetros congelados; solo se ajustan los **577** de la cabeza.',
         '`C` se elige en **val** (si empatan, la menor pérdida logarítmica); test solo se informa.',
         'Registro en la **misma base MLflow** del proyecto: `models/mlflow.db`.'])}</div>
</div>''',
          'Lea la salida de arriba abajo. Los rasgos de 600 fotos tardan menos de un segundo; la cabeza, una décima. Con solo 90 fotos de validación, las cuatro C empatan en exactitud: por eso se desempata con la pérdida logarítmica, que mide si las probabilidades son buenas. Avisos UserWarning o WARNING de MLflow en medio son normales.')

    slide('C', 3, 'Verlo en MLflow', 'C · Paso 4 · navegador', 'Experimento **gato-perro** y modelo registrado', f'''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="capcol">{cap('n04-mlflow.webp', 420)}</div>
 <div class="col">
  {term('Segundo terminal (si no la tienes abierta del laboratorio de MLflow)', ['ir', 'activar', 'ui'])}
  {hazlo(['**Model training** → Experiments → `gato-perro`.', 'Mira parámetros (`C`, `red_base`, `lado`…), métricas (`exactitud_test`…) y, en el modelo, la **firma**.'])}
  {mira(['Firma: entrada `imagen` **uint8 (-1, 128, 128, 3)**; salida `probabilidades` **float32 (-1, 2)**.'])}
 </div>
</div>''',
          'Si la interfaz ya estaba abierta del laboratorio anterior, basta F5. La firma ahora no son 13 columnas sino un tensor: un lote de fotos de 128×128 con 3 canales, en enteros de 0 a 255. Si mlflow_ui dice «Está vacío» (no hay ejecuciones de retencion-90d), en la guía está el plan B con python -m mlflow ui.')

    slide('C', 3, 'Predecir una foto', 'C · Paso 5 · terminal', '`predecir`: del registro a **«gato 0,xx / perro 0,yy»**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('Terminal del Codespace', ['perro', 'gato'])}
  {real('perro', pq=True)}
  {real('gato', pq=True)}
 </div>
 <div class="col capcol">{cap('n05-predecir.webp', 250)}
  {hazlo(['Prueba con **tu foto**: arrástrala al explorador del Codespace y pon su ruta en `predecir`.'])}</div>
</div>''',
          'El script carga la última versión registrada de gato-perro, aplica el mismo recorte y reducción a 128×128 y devuelve las dos probabilidades. El gato abisinio sale 0,55: un caso dudoso, buen pie para la siguiente diapositiva. Anime a probar fotos propias.')

    slide('D', 2, 'Qué significa 93 %', 'D · Leer el resultado', '93 % = **7 de cada 100** fotos fallan', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="card"><h3>Las cifras</h3>{lista([
        'Estudio previo: **93,1 %** en 720 fotos de test (IC95 91,1–94,9 %).',
        'Hoy: **93,3 %** en 90 fotos de test (84 bien, 6 mal). Con tan pocas fotos, unos puntos arriba o abajo son azar.',
        'En validación salió 87,8 % (90 fotos): por eso no se elige con test.'])}</div>
 <div class="card falla"><h3>En producción</h3>{lista([
        'De cada 100 fotos, unas **7 se equivocan**: hay que decidir qué pasa con ellas.',
        'Fotos raras (dos animales, un dibujo, otra especie) no son «ni perro ni gato»: el modelo **siempre** elige uno.',
        'Una probabilidad cerca de 0,5 es una buena señal de duda.'])}</div>
</div>''',
          'Cifras del INFORME y de la ejecución de hoy. Pregunta al grupo: si se usara para algo serio, ¿qué haríamos con las predicciones entre 0,4 y 0,6? Revisión humana, por ejemplo. Y recuerde que una foto de un conejo también saldrá perro o gato.')

    slide('D', 1, 'Siguiente paso', 'D · Hacia producción', 'Siguiente paso: una **API** que reciba la imagen', f'''
<div class="grid3">
 <div class="card"><h3>API con imagen</h3><p class="small">Como la de S2, pero recibiendo un fichero de imagen. En el estudio previo, decodificar, recortar y predecir una foto de 150 KB: 3,9–4,6 ms; a través de FastAPI con su cliente de pruebas, mediana 52 ms.</p></div>
 <div class="card"><h3>ONNX para una imagen ligera</h3><p class="small">Con PyTorch, los paquetes ocupan unos <b>982 MB</b>; exportando a ONNX y sirviendo con ONNX Runtime, unos <b>264 MB</b> (modelo de 3,7 MB).</p></div>
 <div class="card"><h3>Hoy no</h3><p class="small">Sin Docker ni API en este laboratorio: el modelo ya está registrado con su firma, que es lo que necesitaría ese servicio.</p></div>
</div>''',
          'Cifras del INFORME del estudio previo (paquetes descomprimidos en Linux, Python 3.11). Solo como anticipo: el mismo patrón de S2, cambiando la entrada a una imagen y la librería de servicio a ONNX Runtime para no cargar PyTorch en el contenedor.')

    slide('D', 1, 'Autoevaluación', 'Cierre', 'Tres preguntas para llevarte', '''
<div class="grid3">
''' + ''.join(f'<div class="card"><h3>{i}. {md(p)}</h3><details><summary>Ver la respuesta</summary><p class="small">{md(r)}</p></details></div>' for i, (p, r) in enumerate([
        ('¿Qué parte de la red hemos entrenado hoy?', 'Solo la **cabeza** (regresión logística sobre 576 rasgos). MobileNet estaba **congelada**.'),
        ('¿Por qué funciona tan bien con 420 fotos?', 'Por la **transferencia**: MobileNet ya aprendió a ver con ImageNet, que además incluye perros y gatos.'),
        ('¿Qué dice la firma del modelo registrado?', 'Entrada: lote de imágenes **uint8 128×128×3**; salida: **2 probabilidades** (gato, perro).')], 1)) + '</div>',
          'Lea cada pregunta y deje unos segundos antes de desplegar la respuesta. Las fotos quedan en ~/datos-mascotas; se pueden borrar al terminar. La guía en texto queda para repetirlo en casa.')


# =====================================================================================================================================
CSS = r"""
:root{--bg:#ffffff;--text:#1d2733;--muted:#5b6673;--line:#d6dde6;--panel:#f6f8fb;--blue:#1f5fa8;--gold:#9a6a00;
  --ok:#1d7a4f;--bad:#b4323c;--code:#0f1b2a;--codetx:#e6eef8;
  --mono:ui-monospace,"Cascadia Code","SFMono-Regular",Consolas,Menlo,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--sans);overflow:hidden}
button{font:inherit;color:inherit;cursor:pointer;background:none;border:0}
a{color:var(--blue)}
.mono,code,pre{font-family:var(--mono);font-variant-ligatures:none;font-feature-settings:"calt" 0,"liga" 0}
:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
#viewport{position:fixed;left:0;right:0;top:0;bottom:46px;overflow:hidden;background:var(--bg)}
#stage{position:absolute;left:50%;top:50%;width:1280px;height:720px;transform:translate(-50%,-50%) scale(var(--s,1));transform-origin:center}
.slide{position:absolute;inset:0;padding:40px 60px 52px;display:none;background:var(--bg);overflow:hidden}
.slide.active{display:block}
.slide::before{content:"";position:absolute;left:0;right:0;top:0;height:4px;background:var(--blue)}
.kick{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:var(--blue);font-weight:700;margin-bottom:6px}
h1{font-size:34px;line-height:1.15;margin-bottom:18px;font-weight:750}
h1 .mono{font-size:30px}
h3{font-size:17px;margin-bottom:6px;color:var(--text)}
p{font-size:17px;line-height:1.45}
.sub{font-size:22px;line-height:1.4;color:var(--muted)}
.small{font-size:15px;line-height:1.4}
.foot{position:absolute;left:60px;right:60px;bottom:16px;display:flex;justify-content:space-between;font-size:12.5px;letter-spacing:.06em;color:var(--muted);text-transform:uppercase}
.foot b{color:var(--blue)}
.split{display:grid;gap:18px}
.col{display:flex;flex-direction:column;gap:12px;min-width:0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 16px}
.card p{font-size:16px}
.callout{border-left:4px solid var(--blue);background:#eef4fb;padding:10px 14px;border-radius:8px;font-size:17px}
.mira{border-color:#9fd1b7;background:#f1faf5}.mira h3{color:var(--ok)}
.falla{border-color:#ebb7bb;background:#fdf3f4}.falla h3{color:var(--bad)}
.list{list-style:none}.list li{position:relative;padding-left:16px;font-size:15.5px;line-height:1.4;margin:3px 0}
.list li::before{content:"";position:absolute;left:2px;top:9px;width:6px;height:6px;border-radius:50%;background:var(--blue)}
.mira .list li::before{background:var(--ok)}.falla .list li::before{background:var(--bad)}
.tbl{border-collapse:collapse;width:100%;font-size:14.5px}
.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border-bottom:2px solid var(--line);padding:5px 8px}
.tbl td{border-bottom:1px solid var(--line);padding:5px 8px;vertical-align:top;line-height:1.3}
.tbl .mono{font-size:13px}
.term{background:var(--code);border-radius:10px;overflow:hidden;border:1px solid #23344a}
.term .bar{display:flex;align-items:center;gap:8px;padding:6px 10px;background:#1a2a3e;color:#b8c7d9;font-size:12.5px}
.term .bar em{flex:1;font-style:normal}
.tls{padding:6px 8px 8px;font-family:var(--mono);font-size:13.5px;line-height:1.45}
.tln{display:flex;align-items:flex-start;gap:6px;padding:2px 4px}
.tln code{flex:1;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--codetx)}
.tln.c{color:#8fa3b8;font-style:italic}
.ps{color:#7fd4a8}
pre.code{margin:0;padding:8px 12px 10px;font-family:var(--mono);font-size:11.6px;line-height:1.36;color:var(--codetx);white-space:pre-wrap;overflow-wrap:anywhere}
.cp{flex:none;min-width:26px;height:24px;border-radius:6px;border:1px solid #55708f;font-size:13px;color:#d8e4f2;background:#22364e}
.cp.ok{border-color:#7fd4a8;color:#7fd4a8}
.cpall{padding:0 10px;font-family:var(--sans);font-size:12px}
.realbox{border:1px solid #9fd1b7;border-radius:10px;padding:7px 11px;background:#fbfdfc}
.realbox .rk{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--ok);font-weight:700;margin-bottom:3px}
.realbox pre{font-family:var(--mono);font-size:12.2px;line-height:1.38;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--text)}
.realbox.pq pre{font-size:11.6px}
.capcol{gap:10px}
.cap{margin:0;display:flex;flex-direction:column;gap:4px;min-width:0}
.cap figcaption{font-size:12.5px;color:var(--muted)}
.capa{display:block;cursor:zoom-in;padding:0;text-align:left}
.capa img{display:block;max-width:100%;height:auto;border-radius:8px;border:1px solid var(--line);background:#1e1e1e}
.falta{display:flex;flex-direction:column;justify-content:center;align-items:center;gap:4px;min-height:120px;border:2px dashed #b9c3cf;border-radius:8px;background:#f8fafc;color:var(--muted);text-align:center;padding:10px}
.falta b{color:var(--text);font-size:16px}.falta small{font-size:12.5px}
details summary{cursor:pointer;color:var(--blue);font-size:14.5px;margin-top:4px}
details p{margin-top:6px}
svg text.sv-t{font:700 16px var(--sans);fill:var(--text);text-anchor:middle}
svg text.sv-s{font:13px var(--sans);fill:var(--muted);text-anchor:middle}
svg .sv-n{fill:#f6f8fb;stroke:#9fb3c8;stroke-width:1.5}svg .sv-g{fill:#eef4fb;stroke:var(--blue);stroke-width:2}
#bar{position:fixed;left:0;right:0;bottom:0;height:46px;display:flex;align-items:center;gap:6px;padding:0 10px;background:#f3f5f8;border-top:1px solid var(--line);font-size:13.5px}
#bar button,#bar a{padding:5px 10px;border-radius:7px;border:1px solid var(--line);background:#fff;text-decoration:none;color:var(--text)}
#bar .part.on{background:var(--blue);color:#fff;border-color:var(--blue)}
#bar .sp{flex:1}
#count,#clockref{color:var(--muted);padding:0 6px}
#prog{position:fixed;left:0;top:0;height:3px;background:var(--blue);z-index:5}
#notes{position:fixed;right:12px;bottom:56px;width:min(460px,92vw);max-height:60vh;overflow:auto;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:0 8px 30px rgba(0,0,0,.15);display:none;z-index:10}
#notes.on{display:block}#notes p{font-size:15px}
#index{position:fixed;inset:0 0 46px 0;background:rgba(255,255,255,.98);display:none;overflow:auto;padding:24px 30px;z-index:9}
#index.on{display:block}
#idxgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px;margin-top:12px}
#idxgrid button{text-align:left;border:1px solid var(--line);border-radius:9px;padding:8px 10px;background:#fff;font-size:14px}
#idxgrid button small{display:block;color:var(--muted);font-size:12px}
#idxgrid button.cur{border-color:var(--blue);background:#eef4fb}
#zoom{position:fixed;inset:0;background:rgba(10,16,24,.88);display:none;align-items:center;justify-content:center;z-index:20;cursor:zoom-out;padding:20px}
#zoom.on{display:flex}
#zoom img{max-width:100%;max-height:100%;border-radius:6px;background:#1e1e1e}
#zoom p{position:absolute;bottom:10px;left:0;right:0;text-align:center;color:#e6eef8;font-size:14px}
@media print{#bar,#prog,#notes,#index,#zoom,.cp{display:none!important}}
"""

JS = r"""
(function(){
'use strict';
const $=s=>document.querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PARTES=__PARTES__, INICIO=__INICIO__;
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){try{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();return true}catch(e2){return false}}}
const slides=$$('.slide'), N=slides.length;
slides.forEach((s,i)=>{const f=document.createElement('div');f.className='foot';
  f.innerHTML=`<span>ML e IA · S3 · Laboratorio de red neuronal</span><span><b>${esc(PARTES[s.dataset.part])}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
let cur=0;
function go(i){i=Math.max(0,Math.min(N-1,i));cur=i;slides.forEach((s,k)=>s.classList.toggle('active',k===i));chrome();
  try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function chrome(){const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N;
  $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL;
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML='<p>'+esc(s.dataset.notes||'')+'</p>';
  $('#notemin').textContent='Previsto: '+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' de '+TOTAL;
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur))}
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(PARTES[s.dataset.part])} · ${s.dataset.min} min · min ${INICIO+cum[i]}</small>${i+1}. ${esc(s.dataset.title)}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;tog('#index',false);go(+b.dataset.i)});
function tog(sel,force){$(sel).classList.toggle('on',force)}
$('#bprev').onclick=()=>go(cur-1); $('#bnext').onclick=()=>go(cur+1);
$('#bidx').onclick=()=>tog('#index'); $('#bnotes').onclick=()=>tog('#notes');
$('#bfull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else if(document.documentElement.requestFullscreen)document.documentElement.requestFullscreen()};
$$('#bar .part').forEach(b=>b.onclick=()=>go(slides.findIndex(s=>s.dataset.part===b.dataset.p)));
const zoom=$('#zoom');
function cerrarZoom(){zoom.classList.remove('on');$('#zoom img').removeAttribute('src')}
zoom.addEventListener('click',cerrarZoom);
addEventListener('keydown',e=>{
  const t=e.target; if(t&&/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))return; if(e.ctrlKey||e.metaKey||e.altKey)return;
  const k=e.key;
  if(k==='Escape'){if(zoom.classList.contains('on')){cerrarZoom();return}tog('#index',false);tog('#notes',false);return}
  if(zoom.classList.contains('on'))return;
  if(k==='ArrowRight'||k==='PageDown'||(k===' '&&!/^(BUTTON|A|SUMMARY)$/.test(t.tagName))){e.preventDefault();go(cur+1)}
  else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();go(cur-1)}
  else if(k==='Home'){e.preventDefault();go(0)} else if(k==='End'){e.preventDefault();go(N-1)}
  else if(k==='o'||k==='O')tog('#index'); else if(k==='s'||k==='S')tog('#notes'); else if(k==='f'||k==='F')$('#bfull').click();
});
document.addEventListener('click',async e=>{
  const z=e.target.closest('.capa'); if(z){$('#zoom img').src=z.dataset.src;$('#zoom img').alt=z.dataset.alt;$('#zoom p').textContent=z.dataset.alt+' · clic o Esc para cerrar';zoom.classList.add('on');return}
  const b=e.target.closest('.cp'); if(!b)return; e.stopPropagation();
  const ok=await copyText(b.dataset.t); const tx=b.textContent; b.classList.add('ok'); b.textContent=ok?'✓ Copiado':'✗'; setTimeout(()=>{b.classList.remove('ok');b.textContent=tx},1200)});
fit(); const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
})();
"""


def html_completo():
    construir()
    secciones = []
    for s in SLIDES:
        secciones.append(f'<section class="slide" data-part="{s["parte"]}" data-min="{s["min"]}" data-title="{esc(s["titulo"])}"\n'
                         f' data-notes="{esc(s["notas"])}">\n{s["html"]}\n</section>')
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False)).replace('__INICIO__', str(INICIO_SESION))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Laboratorio de red neuronal · S3 · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(secciones) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div id="idxgrid"></div></div>\n'
            '<div id="zoom" role="dialog" aria-label="Captura ampliada"><img alt=""><p></p></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado"></span>\n  {partes}\n  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S3">⌂ S3</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo recorrido está en guia.md.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    faltan = [n for n in CAPTURAS if not (IMG / n).exists()]
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
        print(f'escrito {SALIDA.name}: {len(SLIDES)} diapositivas, {sum(s["min"] for s in SLIDES)} min')
    if faltan:
        print(f'capturas pendientes ({len(faltan)}): ' + ', '.join(faltan))


if __name__ == '__main__':
    main()
