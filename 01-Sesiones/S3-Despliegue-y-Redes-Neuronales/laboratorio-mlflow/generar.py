"""Genera la presentación «Laboratorio de MLflow» (index.html, junto a este archivo).

Bloque de S3 de 45 minutos: qué es MLflow, dónde guarda las cosas el proyecto y, en el Codespace, recorrer el experimento
«retencion-90d», comparar ejecuciones, ver la firma, ver el modelo registrado, crear la versión 2 y cargarla desde Python.
El mismo recorrido, en texto y paso a paso, está en guia.md.

Marco: el mismo de laboratorio-recap-s2 (botón ⧉ para copiar cada orden, teclas ← → · O índice · S notas · F pantalla
completa, reloj de minutos planificados), con fondo blanco y sin efectos al pasar el ratón. Las capturas se amplían con un
clic; Esc o un clic las cierran.

Capturas: img/m01-comprobar.webp … img/m11-cargar.webp (CAPTURAS). Si falta alguna al generar, en su lugar sale un recuadro
«Captura pendiente»: basta con dejar el archivo en img/ y volver a generar.

Salidas: son REALES, de la ejecución en local (Windows, entorno env-ia-mlops, MLflow 3.18.0, muestra del curso, carpeta
temporal, 20/11/2026) de las mismas órdenes. Lo que se ve en la web de MLflow no se transcribe: se remite a la captura.

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
LOCAL = f'Salida real · Codespace del curso y local · {FECHA}'
INICIO_SESION = 0           # minuto de la sesión en que empieza el bloque (el reloj cuenta desde aquí)
DURACION = 45

# Las capturas del Codespace (nombre → qué enseña). Son las únicas imágenes que puede citar la presentación.
CAPTURAS = {
    'm01-comprobar.webp': 'Terminal: mlflow_ui --comprobar',
    'm02-arrancar.webp': 'Terminal: la interfaz de MLflow arrancada',
    'm03-inicio.webp': 'Página de inicio de MLflow: GenAI | Model training',
    'm04-experimento.webp': 'Experimento retencion-90d con la lista de ejecuciones',
    'm05-run-detalle.webp': 'Una ejecución: parámetros y métricas',
    'm06-comparar.webp': 'Comparación de dos ejecuciones',
    'm07-artefactos.webp': 'Artefactos del modelo y su firma',
    'm08-modelos.webp': 'Modelo registrado retencion-90d con sus versiones',
    'm09-forzar.webp': 'Terminal: pipeline_train --forzar crea la versión 2',
    'm10-version2.webp': 'Versiones 1 y 2 en la interfaz',
    'm11-cargar.webp': 'Terminal: cargar el modelo registrado y predecir',
}

# --- Órdenes (las mismas en la guía; la prueba comprueba que los módulos y rutas existen) --------------------------------------
RAIZ_CS = '/workspaces/curso-ml-ia-desarrollo-produccion/04-Proyecto-Base'
O = {
    'ir': f'cd {RAIZ_CS}',
    'activar': 'conda activate env-ia-mlops',
    'pipeline': 'python -m ia_mlops.pipeline',
    'comprobar': 'python -m ia_mlops.mlflow_ui --comprobar',
    'ui': 'python -m ia_mlops.mlflow_ui',
    'ui5001': 'python -m ia_mlops.mlflow_ui --port 5001',
    'train': 'python -m ia_mlops.pipeline_train',
    'forzar': 'python -m ia_mlops.pipeline_train --forzar',
}

# Plan B, NO verificado en el Codespace: solo si la web dice «Invalid Host header».
UI_HOSTS = ('python -m mlflow ui --backend-store-uri "$(python -c \'from ia_mlops import mlflow_ui; print(mlflow_ui.uri())\')" '
            "--port 5000 --allowed-hosts '*' --cors-allowed-origins '*'")

# Cargar el modelo REGISTRADO (no la carpeta models/modelo_mlflow) y predecir el cliente de ejemplo. Probado tal cual en local.
CARGAR = """python - <<'EOF'
import json, warnings
warnings.filterwarnings('ignore')
import mlflow, mlflow.sklearn
import pandas as pd
from ia_mlops import config, mlflow_ui

mlflow.set_tracking_uri(mlflow_ui.uri())          # la base DEL PROYECTO, con ruta absoluta
nombre = config.MODELO_REGISTRADO                 # 'retencion-90d'
versiones = mlflow.MlflowClient().search_model_versions(f"name='{nombre}'")
ultima = max(int(v.version) for v in versiones)
print(f'Modelo registrado {nombre}: versiones {sorted(int(v.version) for v in versiones)}; cargo la {ultima}')

uri = f'models:/{nombre}/{ultima}'
firma = mlflow.models.get_model_info(uri).signature
print('Firma:', len(firma.inputs.inputs), 'entradas ->', firma.outputs.inputs[0].type)

modelo = mlflow.sklearn.load_model(uri)
cliente = json.load(open('tests/datos/cliente_ejemplo.json'))
fila = pd.DataFrame([cliente])[config.FEATURES]
print(f'Probabilidad de recompra en 90 días (cliente de ejemplo): {modelo.predict_proba(fila)[0, 1]:.3f}')
EOF"""

# --- Salidas reales (en local, Windows, env-ia-mlops, MLflow 3.18.0, 20/11/2026) --------------------------------------------
SALIDAS = {
    'comprobar': ('Registro de MLflow: …/04-Proyecto-Base/models/mlflow.db\n'
                  '  Experimento «retencion-90d»: 4 ejecuciones · modelo registrado «retencion-90d»: 1 versiones'),
    'sin_base': '  No existe todavía. Entrena primero:  python -m ia_mlops.pipeline   (o ejecuta el cuaderno 04 con USAR_MLFLOW = True)',
    'ui': ('Registro de MLflow: …/04-Proyecto-Base/models/mlflow.db\n'
           '  Experimento «retencion-90d»: 4 ejecuciones · modelo registrado «retencion-90d»: 1 versiones\n'
           'Abriendo http://127.0.0.1:5000  ·  En la web elige «Model training» (arriba a la izquierda).  ·  Para parar: Ctrl+C'),
    'sin_cambios': '[pipeline_train] sin cambios: la entrada es la misma que en la ultima ejecucion (7108eeb2fa32). Usa --forzar para rehacerlo.',
    'forzar': ('[pipeline_train] ejecutando (huella de entrada 7108eeb2fa32)\n'
               '  referencia_sin_aprender    AUC valid 0.500 | test 0.500 | precision media test 0.404\n'
               '  regresion_logistica        AUC valid 0.698 | test 0.747 | precision media test 0.659\n'
               '  gradient_boosting          AUC valid 0.663 | test 0.735 | precision media test 0.648\n'
               "Registered model 'retencion-90d' already exists. Creating a new version of this model...\n"
               "Created version '2' of model 'retencion-90d'.\n"
               '  Mejor modelo: regresion_logistica. Guardado en …/models/modelo.joblib\n'
               '  Registrado en MLflow como «retencion-90d», version 2. Para verlo: python -m ia_mlops.mlflow_ui'),
    'comprobar2': ('Registro de MLflow: …/04-Proyecto-Base/models/mlflow.db\n'
                   '  Experimento «retencion-90d»: 8 ejecuciones · modelo registrado «retencion-90d»: 2 versiones'),
    'cargar': ('Modelo registrado retencion-90d: versiones [1, 2]; cargo la 2\n'
               'Firma: 13 entradas -> float64\n'
               'Probabilidad de recompra en 90 días (cliente de ejemplo): 0.828'),
}

# Valores reales de las ejecuciones (muestra del curso, huella_datos 35a94deb4e04ab4a), leídos de la base con MlflowClient.
METRICAS = [
    ['referencia_sin_aprender', '0,500', '0,500', '0,500', '0,456'],
    ['regresion_logistica', '0,803', '**0,698**', '0,747', '0,736'],
    ['gradient_boosting', '1,000', '0,663', '0,735', '0,704'],
]


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código` y **negrita** a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)


def term(titulo, claves):
    """Terminal: una orden por línea con su ⧉. Una clave que empieza por # es un comentario."""
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


def bloque(titulo, texto):
    """Un programa de varias líneas que se copia entero con un solo ⧉."""
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em>'
            f'<button class="cp cpall" data-t="{esc(texto)}">⧉ Copiar la orden entera</button></div>'
            f'<pre class="code">{esc(texto)}</pre></div>')


def real(clave, fuente=LOCAL, pq=False):
    return f'<div class="realbox{" pq" if pq else ""}"><div class="rk">{esc(fuente)}</div><pre>{esc(SALIDAS[clave])}</pre></div>'


def cap(nombre, alto=None):
    """Captura del Codespace: se amplía con un clic. Si aún no está en img/, recuadro «Captura pendiente»."""
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


PARTES = {'A': 'Qué es', 'B': 'Dónde vive', 'C': 'Práctica', 'D': 'Cierre'}
SLIDES = []


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    SLIDES.append(dict(parte=parte, min=minutos, titulo=titulo, notas=notas,
                       html=f'<p class="kick">{esc(kick)}</p><h1>{md(h1)}</h1>\n{cuerpo}'))


def svg_mapa():
    """train.py escribe en el seguimiento (experimento → ejecuciones) y registra el mejor (registro → versiones)."""
    o = ['<defs><marker id="fm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0 L10 5 L0 10 z" fill="#1f5fa8"/></marker></defs>']

    def caja(x, y, w, h, t, s, c):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="sv-{c}"/>'
                 f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" class="sv-t">{esc(t)}</text>'
                 f'<text x="{x + w / 2}" y="{y + h / 2 + 18}" class="sv-s">{esc(s)}</text>')

    def flecha(x1, y1, x2, y2):
        o.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="#1f5fa8" stroke-width="2.5" fill="none" marker-end="url(#fm)"/>')

    caja(10, 95, 190, 80, 'train.py', 'pipeline_train', 'n')
    caja(250, 10, 220, 80, 'Experimento', 'retencion-90d', 'g')
    caja(520, 10, 290, 80, 'Ejecuciones (runs)', '3 modelos + MEJOR-<modelo>', 'n')
    caja(860, 10, 270, 80, 'En cada una', 'parámetros · métricas', 'n')
    caja(250, 180, 220, 80, 'Modelo + firma', 'artefactos del MEJOR', 'n')
    caja(520, 180, 290, 80, 'Modelo registrado', 'retencion-90d', 'g')
    caja(860, 180, 270, 80, 'Versiones', '1, 2, 3… (+ etiquetas)', 'n')
    flecha(200, 120, 246, 60)
    flecha(200, 150, 246, 210)
    flecha(470, 50, 516, 50)
    flecha(810, 50, 856, 50)
    flecha(470, 220, 516, 220)
    flecha(810, 220, 856, 220)
    o.append('<text x="690" y="130" class="sv-s">SEGUIMIENTO (tracking): ¿qué probé y qué salió?</text>'
             '<text x="690" y="290" class="sv-s">REGISTRO (Model Registry): ¿qué modelo uso y de dónde salió?</text>')
    return f'<svg viewBox="0 0 1140 300" role="img" aria-label="Seguimiento y registro de MLflow">{"".join(o)}</svg>'


def svg_almacen():
    o = ['<defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0 L10 5 L0 10 z" fill="#1f5fa8"/></marker></defs>']
    for x, t, s1, s2, c in [(10, 'train.py', 'escribe', '', 'n'),
                             (330, 'models/mlflow.db', 'SQLite: experimentos, runs,', 'parámetros, métricas, registro', 'g'),
                             (330, 'models/mlartifacts/', 'archivos: MLmodel, model.pkl,', 'firma, requisitos', 'g'),
                             (750, 'mlflow_ui', 'lee y enseña', '(puerto 5000)', 'n')]:
        y = 120 if x == 330 and t.endswith('/') else 10
        if x != 330:
            y = 65
        o.append(f'<rect x="{x}" y="{y}" width="300" height="90" rx="12" class="sv-{c}"/>'
                 f'<text x="{x + 150}" y="{y + 32}" class="sv-t">{esc(t)}</text>'
                 f'<text x="{x + 150}" y="{y + 56}" class="sv-s">{esc(s1)}</text>'
                 f'<text x="{x + 150}" y="{y + 75}" class="sv-s">{esc(s2)}</text>')
    for d in ('M310 100 L326 60', 'M310 120 L326 160', 'M630 60 L746 100', 'M630 160 L746 120'):
        o.append(f'<path d="{d}" stroke="#1f5fa8" stroke-width="2.5" fill="none" marker-end="url(#fa)"/>')
    return f'<svg viewBox="0 0 1060 220" role="img" aria-label="Dónde guarda MLflow los datos del proyecto">{"".join(o)}</svg>'


# =====================================================================================================================================
def construir():
    SLIDES.clear()

    # ------------------------------------------------------------------------------------------------ A · Qué es
    slide('A', 2, 'Portada', 'S3 · Laboratorio de MLflow', 'MLflow: el **cuaderno de laboratorio** del modelo', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  <p class="sub">En 45 minutos abres en tu Codespace el MLflow del proyecto: ves qué se entrenó, comparas los modelos, miras la firma, creas la versión 2 de «retencion-90d» y la cargas desde Python.</p>
  <div class="card"><h3>Cómo seguirla</h3>{lista([
        'Cada orden lleva **⧉**: cópiala y pégala en el terminal del Codespace.',
        f'Las salidas de terminal son **reales** (en local, {FECHA}) y las capturas, de un **Codespace del curso**. Clic en una captura para ampliarla; **Esc** la cierra.',
        'El mismo recorrido en texto, para repetirlo solo: `laboratorio-mlflow/guia.md`.',
        'Teclas: **← →** avanzar · **O** índice · **S** notas · **F** pantalla completa.'])}</div>
 </div>
 <div class="card"><h3>Palabras de hoy</h3>{tabla(['Palabra', 'Qué es'], [
        ['**Experimento**', 'Carpeta de intentos de un mismo problema: `retencion-90d`.'],
        ['**Ejecución (run)**', 'Un entrenamiento concreto, con sus parámetros y métricas.'],
        ['**Artefacto**', 'Un archivo guardado por la ejecución: aquí, el modelo.'],
        ['**Firma**', 'El contrato del modelo: nombre y tipo de cada entrada y de la salida.'],
        ['**Registro**', 'Catálogo de modelos con **versiones** numeradas.'],
        ['**URI**', 'Identificador de recurso: la «dirección» de la base o del modelo.']])}</div>
</div>''',
          'Bienvenida. Este laboratorio retoma lo que en S1 no llegó a verse bien: la interfaz de MLflow. El ejemplo es el de siempre, Online Retail II y el modelo registrado retencion-90d. Recuerde que la guía en texto permite seguir solo a quien se quede atrás.')

    slide('A', 3, 'Por qué MLflow', 'A · La idea', 'Sin MLflow: «¿qué modelo era el bueno?»', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card falla"><h3>Sin seguimiento</h3>{lista([
        'Entrenas tres modelos; el AUC queda en el terminal y se pierde.',
        'Una semana después nadie sabe **con qué datos** se entrenó el que está en la API.',
        'El archivo `modelo.joblib` se sobrescribe: no hay vuelta atrás.'])}</div>
 </div>
 <div class="col">
  <div class="card mira"><h3>Con MLflow (lo hace train.py)</h3>{lista([
        '**Seguimiento**: cada entrenamiento deja una ejecución con **parámetros** (lo decidido antes) y **métricas** (lo medido después).',
        'La `huella_datos` en cada ejecución: con qué datos exactos se entrenó.',
        '**Registro**: el elegido se guarda como `retencion-90d` y cada entrenamiento crea una **versión** nueva; las anteriores no se borran.',
        'La **firma** viaja con el modelo: la API comprueba con ella su contrato (S2).'])}</div>
 </div>
</div>''',
          'La pregunta que resuelve MLflow es de trazabilidad: qué probé, qué salió y qué modelo está en uso. Parámetros son lo que se decide antes de entrenar; métricas, lo que se mide después. Relacione la firma con la API de S2: el servicio no arranca si el esquema no coincide con la firma.')

    slide('A', 2, 'Seguimiento y registro', 'A · El mapa', 'Dos piezas: **seguimiento** y **registro**', f'''
<div class="card" style="padding:14px 16px">{svg_mapa()}</div>
<div class="grid3" style="margin-top:14px">
 <div class="card"><h3>Parámetros (train.py)</h3><p class="small"><span class="mono">modelo</span>, <span class="mono">ventana_objetivo_dias</span>, <span class="mono">n_variables</span>, <span class="mono">huella_datos</span>.</p></div>
 <div class="card"><h3>Métricas: partición_métrica</h3><p class="small"><span class="mono">train_ / valid_ / test_</span> + <span class="mono">auc</span>, <span class="mono">precision_media</span>, <span class="mono">tasa_base</span>, <span class="mono">aciertos_en_el_10_mejor</span>: 12 por ejecución.</p></div>
 <div class="card"><h3>Etiquetas de cada versión</h3><p class="small"><span class="mono">modelo</span>, <span class="mono">huella_datos</span> y <span class="mono">valid_auc</span>.</p></div>
</div>''',
          'Recorra el diagrama. Arriba el seguimiento: un experimento, cuatro ejecuciones por entrenamiento (los tres modelos y MEJOR-regresion_logistica). Abajo el registro: solo el mejor, como versión nueva de retencion-90d, con tres etiquetas. Los nombres son los de ia_mlops/modeling/train.py; la ejecución MEJOR-… solo lleva los parámetros modelo y huella_datos.')

    # ------------------------------------------------------------------------------------------------ B · Dónde vive
    slide('B', 4, 'Dónde vive', 'B · Dónde lo guarda el proyecto', 'Dos sitios en `models/`, y **una ruta absoluta**', f'''
<div class="card" style="padding:12px 16px">{svg_almacen()}</div>
<div class="split" style="grid-template-columns:1fr 1fr;margin-top:12px">
 <div class="card"><h3>Por qué <span class="mono">python -m ia_mlops.mlflow_ui</span></h3>{lista([
        '`mlflow ui --backend-store-uri sqlite:///models/mlflow.db` usa una ruta **relativa**: lanzado desde la raíz del repositorio, crea **otra base vacía** sin avisar.',
        '`mlflow_ui` calcula la ruta **absoluta** (`config.MODELOS`), comprueba que hay ejecuciones y solo entonces arranca la web.',
        'Es la misma base en la que escribe `train.py`.'])}</div>
 <div class="card"><h3>Ni hay que crearla ni se edita a mano</h3>{lista([
        'La crea el **primer entrenamiento** con MLflow (`python -m ia_mlops.pipeline`).',
        'La web **lee la base cada vez**: tras entrenar basta con **F5**.',
        'Empezar de cero: borrar `models/mlflow.db` **y** `models/mlartifacts/`, los dos.'])}</div>
</div>''',
          'Este es el porqué de lo que falló en S1: la interfaz leía una base vacía creada por una ruta relativa. Insista: siempre desde 04-Proyecto-Base y siempre con python -m ia_mlops.mlflow_ui. mlflow.db es el backend store (metadatos) y mlartifacts el artifact store (archivos). En MLflow 3 el modelo guardado está en mlartifacts/models/m-<identificador>/artifacts.')

    # ------------------------------------------------------------------------------------------------ C · Práctica
    slide('C', 2, 'Comprobar el registro', 'C · Paso 1 · terminal', '¿Qué hay en el registro? **--comprobar**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('Terminal del Codespace', ['ir', 'activar', 'comprobar'])}
  {real('comprobar', pq=True)}
  {falla(['«No existe todavía»: entrena primero con `python -m ia_mlops.pipeline` (≈ 30 s de entrenamiento) y repite.',
          '`No module named ia_mlops`: no estás en `04-Proyecto-Base`.'])}
 </div>
 <div class="col capcol">{cap('m01-comprobar.webp', 300)}
  {mira(['**4 ejecuciones** (3 modelos + `MEJOR-…`) y **1 versión**, si has entrenado una vez.', 'Si has entrenado más veces verás más: es normal.'])}</div>
</div>''',
          'No abre nada: solo lee la base y cuenta. Es la comprobación que evita la confusión de S1. Si alguien tiene «No existe todavía», que lance el pipeline ahora; tarda poco con la muestra. En el Codespace del profesor salió lo mismo: 4 ejecuciones y 1 versión.')

    slide('C', 3, 'Arrancar la interfaz', 'C · Paso 2 · terminal T1', 'La web de MLflow, en el **puerto 5000**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T1 · la interfaz (se queda ocupada: no la cierres)', ['ui'])}
  {real('ui', pq=True)}
  {hazlo(['Pestaña **Puertos** → fila **5000** → icono del globo.', 'Abre un **segundo terminal** (T2) para los pasos 8 y 9.'])}
  {falla(['Página en blanco: la primera carga tarda unos **10 s**; espera y pulsa **F5**.',
          'Puerto ocupado: `python -m ia_mlops.mlflow_ui --port 5001`.',
          '«Invalid Host header» (no visto en el Codespace del curso): plan B en la guía, apartado «Si falla».'])}
 </div>
 <div class="col capcol">{cap('m02-arrancar.webp', 330)}</div>
</div>''',
          'Por dentro lanza mlflow ui con la ruta absoluta, con el mismo Python del entorno. Debajo de «Abriendo…» salen los mensajes del servidor de MLflow (se ven en la captura). Para parar: Ctrl+C en T1. Comprobado en el Codespace: el puerto 5000 reenviado funciona; la primera carga tarda unos diez segundos.')

    slide('C', 2, 'Model training', 'C · Paso 3 · navegador', 'Primero: pulsa **Model training**', f'''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="capcol">{cap('m03-inicio.webp', 420)}</div>
 <div class="col">
  {hazlo(['Arriba a la izquierda, el conmutador **GenAI | Model training**: pulsa **Model training**.',
          'El menú izquierdo cambia (según la captura): ahí están los experimentos y el registro de modelos.'])}
  {falla(['Ves menús de IA generativa (trazas, prompts…): sigues en **GenAI**.',
          'No hay experimentos: estás leyendo otra base. Ctrl+C en T1 y vuelve al paso 1 desde `04-Proyecto-Base`.'])}
 </div>
</div>''',
          'MLflow 3 abre en el modo de IA generativa, que no enseña entrenamientos clásicos. Es la segunda causa de «no se ve nada» en S1. Que todos pulsen Model training antes de seguir.')

    slide('C', 3, 'El experimento', 'C · Paso 4 · navegador', 'Experimento **retencion-90d**: una fila por ejecución', f'''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="capcol">{cap('m04-experimento.webp', 420)}</div>
 <div class="col">
  {hazlo(['**Experiments** → `retencion-90d` (el experimento `Default` lo crea MLflow solo y está vacío).',
          'Con **Columns** añade `valid_auc`, `test_auc` y `huella_datos`.'])}
  {mira(['Cuatro ejecuciones: `referencia_sin_aprender`, `regresion_logistica`, `gradient_boosting` y `MEJOR-regresion_logistica`.',
         'La `MEJOR-…` es la que tiene el modelo registrado (según la captura, en su columna de modelos).',
         'Todas con la misma `huella_datos`: se entrenaron con los mismos datos.'])}
 </div>
</div>''',
          'Los nombres de las ejecuciones son run_name de train.py: uno por modelo y MEJOR-<modelo> para el elegido. Haga notar la huella: si no coincide entre dos ejecuciones, compararlas no es justo.')

    slide('C', 3, 'Detalle de una ejecución', 'C · Paso 5 · navegador', 'Dentro de una ejecución: **parámetros** y **métricas**', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="capcol">{cap('m05-run-detalle.webp', 420)}</div>
 <div class="col">
  {hazlo(['Clic en `regresion_logistica`.'])}
  {mira(['**Parámetros**: `modelo`, `ventana_objetivo_dias` = 90, `n_variables` = 13, `huella_datos`.',
         '**Métricas**: 12, `train_`, `valid_` y `test_` de `auc`, `precision_media`, `tasa_base` y `aciertos_en_el_10_mejor`.',
         'Con la muestra: `valid_auc` 0,698 y `test_auc` 0,747.'])}
  <div class="card"><p class="small"><b>aciertos_en_el_10_mejor</b>: de los clientes con el 10 % de probabilidades más altas, cuántos compraron de verdad. <b>tasa_base</b>: la proporción de compradores, el listón.</p></div>
 </div>
</div>''',
          'Lea un parámetro y una métrica en voz alta y diga de qué línea de train.py salen: log_param y log_metric con el prefijo de la partición. Los valores son los de la muestra del curso; con otros datos cambian.')

    slide('C', 4, 'Comparar ejecuciones', 'C · Paso 6 · navegador', '**Compare**: regresión logística frente a boosting', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col capcol">{cap('m06-comparar.webp', 300)}
  {hazlo(['Vuelve a la lista, marca `regresion_logistica` y `gradient_boosting` y pulsa **Compare**.'])}</div>
 <div class="col">
  <div class="card"><h3>Valores reales (muestra del curso)</h3>{tabla(['Ejecución', 'train_auc', 'valid_auc', 'test_auc', 'valid_precision_media'], METRICAS)}</div>
  {mira(['El boosting saca **1,000 en train** y 0,663 en valid: ha **memorizado** (sobreajuste).',
         'Gana la regresión logística por **más AUC en valid**. Test se informa, no se usa para elegir.',
         'La referencia (0,500) es el mínimo que hay que superar.'])}
 </div>
</div>''',
          'Esta es la diapositiva del porqué del modelo elegido. Pregunte al grupo: ¿por qué no elegimos por test? Porque dejaría de ser un examen sorpresa. ¿Qué indica train 1,000 y valid 0,663? Sobreajuste.')

    slide('C', 3, 'Artefactos y firma', 'C · Paso 7 · navegador', 'El modelo guardado y su **firma**', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="capcol">{cap('m07-artefactos.webp', 420)}</div>
 <div class="col">
  {hazlo(['Abre `MEJOR-regresion_logistica` y, desde ella, el modelo `modelo` y sus **artefactos** (según la captura).'])}
  {mira(['Archivos: `MLmodel`, `model.pkl`, `input_example.json`, `serving_input_example.json`, `conda.yaml`, `python_env.yaml`, `requirements.txt`.',
         'Firma: **13 entradas** (`long` o `double`; `dias_medios_entre_compras` no obligatoria) y **1 salida** `float64`: la probabilidad.',
         'En disco: `models/mlartifacts/models/m-<id>/artifacts/`.'])}
  <div class="card"><p class="small">En MLflow 3 el modelo no cuelga de la carpeta del run: es un «modelo registrado en la ejecución» con su propio identificador <span class="mono">m-…</span>.</p></div>
 </div>
</div>''',
          'La firma es el contrato: las mismas 13 variables de config.FEATURES. La API de S2 la lee de models/modelo_mlflow y no arranca si no coincide con su esquema. La firma se infiere de 200 filas de train; por eso aparecen tipos long y double.')

    slide('C', 2, 'El modelo registrado', 'C · Paso 8 · navegador', 'Registro: **retencion-90d**, versión 1', f'''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="capcol">{cap('m08-modelos.webp', 420)}</div>
 <div class="col">
  {hazlo(['Menú izquierdo: registro de modelos → `retencion-90d` (o `http://…:5000/#/models`).'])}
  {mira(['Una fila por versión: **Version 1**.',
         'Etiquetas de la versión: `modelo` = regresion_logistica, `huella_datos`, `valid_auc` = 0.6982.',
         'Desde la versión se llega a la ejecución `MEJOR-…` de la que salió.'])}
 </div>
</div>''',
          'El registro responde a otra pregunta que el seguimiento: no qué probé, sino qué modelo uso. Las etiquetas las pone train.py con set_model_version_tag. En S4 y S5 se añadirá un alias a una versión.')

    slide('C', 3, 'Reentrenar: versión 2', 'C · Paso 9 · terminal T2', 'Reentrenar con **--forzar** → versión 2', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T2 · con la interfaz abierta en T1', ['ir', 'train', 'forzar', 'comprobar'])}
  {real('sin_cambios', pq=True)}
  {real('forzar', pq=True)}
 </div>
 <div class="col capcol">{cap('m09-forzar.webp', 250)}
  {real('comprobar2', pq=True)}
  {mira(['Sin `--forzar`: «sin cambios». El pipeline es **idempotente**: mismos datos y mismo código, no entrena.',
         'Con `--forzar`: 4 ejecuciones más y la **versión 2** de `retencion-90d`.',
         'Avisos `UserWarning` y `WARNING` de MLflow en medio: son normales, no errores.'])}</div>
</div>''',
          'Idempotencia: la huella de entrada no cambió, así que pipeline_train no repite el trabajo ni ensucia MLflow. --forzar entrena igualmente. Los resultados son idénticos a la versión 1 porque los datos y el código son los mismos: lo que cambia es que hay una versión nueva, enlazada a su propia ejecución.')

    slide('C', 2, 'Versiones 1 y 2', 'C · Paso 10 · navegador', 'F5: **dos versiones** en el registro', f'''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="capcol">{cap('m10-version2.webp', 420)}</div>
 <div class="col">
  {hazlo(['En el navegador, **F5** en `retencion-90d`. No hace falta reiniciar `mlflow_ui`.'])}
  {mira(['**Version 1** y **Version 2**, con las mismas etiquetas (mismos datos, mismo resultado).',
         'En el experimento: **8 ejecuciones**.', 'La versión 1 **no se borra**: se podría volver a ella.'])}
 </div>
</div>''',
          'La web lee la base en cada petición: basta con recargar. Pregunta: si la versión 2 fuera peor, ¿qué haríamos? Volver a la 1; en S4 y S5 eso se hace moviendo un alias, sin reentrenar.')

    slide('C', 3, 'Cargar el modelo registrado', 'C · Paso 11 · terminal T2', 'Del registro a una **predicción**, desde Python', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">{bloque('T2 · pega la orden entera (de python a EOF)', CARGAR)}
  {falla(['Se queda con `>`: falta la última línea, `EOF`. «Modelo no encontrado»: no usas la base del proyecto (`mlflow_ui.uri()`).'])}</div>
 <div class="col">
  {real('cargar')}
  {cap('m11-cargar.webp', 170)}
  {mira(['Carga `models:/retencion-90d/2` con la URI de la base del proyecto (`mlflow_ui.uri()`).',
         '**0,828**: la misma probabilidad que da la API de S2 para `cliente_ejemplo.json` (0.8278889…).'])}
 </div>
</div>''',
          'Explique tres líneas: set_tracking_uri con la ruta absoluta, la URI models:/nombre/versión y predict_proba. Se usa mlflow.sklearn.load_model a propósito: con mlflow.pyfunc, predict devolvería la clase 0 o 1, no la probabilidad. La API de S2 no lee el registro: carga la copia models/modelo_mlflow, que train.py exporta con la misma firma.')

    # ------------------------------------------------------------------------------------------------ D · Cierre
    slide('D', 2, 'Qué aporta en producción', 'D · Hacia S4 y S5', 'En producción: **qué versión** está sirviendo', f'''
<div class="grid3">
 <div class="card"><h3>Trazabilidad</h3><p class="small">Cada versión apunta a su ejecución: parámetros, métricas y <b>huella de los datos</b>. Ante una predicción rara se sabe qué modelo fue.</p></div>
 <div class="card"><h3>Alias (S4 y S5)</h3><p class="small">Se pone un alias, por ejemplo <span class="mono">produccion</span>, a una versión. El despliegue carga el alias, no un número fijo.</p></div>
 <div class="card"><h3>Vuelta atrás</h3><p class="small">Si la versión nueva falla, se mueve el alias a la anterior. No se reentrena ni se borra nada.</p></div>
</div>
<div class="callout" style="margin-top:14px">Hoy la API carga la carpeta <span class="mono">models/modelo_mlflow</span>; en S4 y S5 se desplegará una <b>versión concreta</b> del registro.</div>''',
          'Cierre conceptual. Lo que hoy hemos hecho a mano con un número de versión es lo que en S4 y S5 se hará con alias y despliegue de una versión concreta. No entre en detalle: es el anticipo.')

    slide('D', 2, 'Autoevaluación', 'Cierre', 'Cuatro preguntas para llevarte', '''
<div class="grid2">
''' + ''.join(f'<div class="card"><h3>{i}. {md(p)}</h3><details><summary>Ver la respuesta</summary><p class="small">{md(r)}</p></details></div>' for i, (p, r) in enumerate([
        ('¿Qué diferencia hay entre un parámetro y una métrica?', 'El parámetro se decide **antes** de entrenar (`modelo`, `n_variables`…); la métrica se mide **después** (`valid_auc`…).'),
        ('¿Por qué `python -m ia_mlops.mlflow_ui` y no `mlflow ui` a pelo?', 'Porque calcula la ruta **absoluta** de `models/mlflow.db`; con la relativa, desde otra carpeta, MLflow crea una base vacía sin avisar.'),
        ('¿Por qué sin `--forzar` no se creó la versión 2?', 'El pipeline es idempotente: mismos datos y mismo código → «sin cambios», no entrena.'),
        ('¿Qué es la firma y quién la usa?', 'El contrato de entrada y salida del modelo (13 entradas, 1 salida). La API la comprueba al arrancar.')], 1)) + '</div>',
          'Lea cada pregunta y deje unos segundos antes de desplegar la respuesta. Para cerrar: Ctrl+C en T1 para parar la interfaz. La guía en texto queda para repetirlo en casa.')


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
  f.innerHTML=`<span>ML e IA · S3 · Laboratorio de MLflow</span><span><b>${esc(PARTES[s.dataset.part])}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
const hm=m=>Math.floor(m/60)+':'+String(m%60).padStart(2,'0');
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
            '<title>Laboratorio de MLflow · S3 · ML e IA: de desarrollo a producción</title>\n'
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
