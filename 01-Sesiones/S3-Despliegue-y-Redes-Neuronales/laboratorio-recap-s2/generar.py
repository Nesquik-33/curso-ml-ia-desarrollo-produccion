"""Genera la presentación «Laboratorio-recap de S2» (index.html, junto a este archivo).

Es el primer bloque de S3 (90 min, de 0:10 a 1:40 de la sesión): repasar S2 haciéndolo otra vez en el Codespace.
Tres demostraciones: la inferencia con la API, el cálculo al vuelo de las variables de la capa FS y la interfaz de consulta.
El mismo recorrido, en texto y paso a paso, está en guia.md.

Marco: el de la presentación de S2 «Del ordenador al servicio» (botón ⧉ para copiar cada orden, teclas ← → · O índice ·
S notas · F pantalla completa, reloj de minutos planificados), aquí con fondo blanco y sin efectos al pasar el ratón.
Las capturas se amplían al hacer clic; Esc o un clic las cierran.

Capturas: img/r01-codespace.webp … img/r13-listo-503.webp (CAPTURAS). Si falta alguna al generar, en su lugar sale un
recuadro «Captura pendiente»: basta con dejar el archivo en img/ y volver a generar.

Salidas: todas son REALES, de la ejecución en local (Windows, entorno env-ia-mlops, 20/11/2026) de las mismas órdenes.
Si cambian, se actualizan en SALIDAS y se regenera.

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
LOCAL = f'Salida real · en local (Windows) · {FECHA}'
INICIO_SESION = 10          # el bloque empieza en el minuto 10 de la sesión (10:10 hora de Perú)
DURACION = 90

# Las capturas del Codespace (nombre → qué enseña). Son las únicas imágenes que puede citar la presentación.
CAPTURAS = {
    'r01-codespace.webp': 'Codespace abierto con el terminal',
    'r02-pipeline.webp': 'Final de operacional y pipeline',
    'r03-api-arrancada.webp': 'uvicorn escuchando en el puerto 8080',
    'r04-puertos.webp': 'Pestaña Puertos con el 8080 y el 8090',
    'r05-docs.webp': 'Página /docs de la API',
    'r06-predecir.webp': 'curl a /predecir y su respuesta',
    'r07-lote.webp': 'curl a /predecir/lote',
    'r08-fs-al-vuelo.webp': 'El fragmento de FS al vuelo en el terminal',
    'r09-interfaz-13599.webp': 'La interfaz con el cliente 13599',
    'r10-interfaz-variables.webp': 'Las 13 variables del 13599 en la interfaz',
    'r11-interfaz-ejemplo.webp': 'El botón Ejemplo: tres tramos y un id que no existe',
    'r12-interfaz-corte.webp': 'La interfaz con la fecha de corte cambiada',
    'r13-listo-503.webp': 'API parada: /salud 200 y /listo 503',
}

# --- Órdenes (las mismas en la guía; la prueba comprueba que los módulos y rutas existen) --------------------------------------
RAIZ_CS = '/workspaces/curso-ml-ia-desarrollo-produccion/04-Proyecto-Base'
O = {
    'ir': f'cd {RAIZ_CS}',
    'activar': 'conda activate env-ia-mlops',
    'ver': 'pwd && python --version && ls',
    'preparar': 'python -m ia_mlops.operacional && python -m ia_mlops.pipeline',
    'api': 'python -m uvicorn ia_mlops.api.app:app --host 127.0.0.1 --port 8080',
    'salud': 'curl -s http://127.0.0.1:8080/salud; echo',
    'listo': 'curl -s http://127.0.0.1:8080/listo; echo',
    'modelo': 'curl -s http://127.0.0.1:8080/modelo | python -m json.tool | head -n 25',
    'predecir': 'curl -s -X POST http://127.0.0.1:8080/predecir -H "Content-Type: application/json" -d @tests/datos/cliente_ejemplo.json; echo',
    'lote': 'curl -s -X POST http://127.0.0.1:8080/predecir/lote -H "Content-Type: application/json" -d @tests/datos/lote_ejemplo.json; echo',
    'p422': "curl -s -w ' [%{http_code}]\\n' -X POST http://127.0.0.1:8080/predecir -H \"Content-Type: application/json\" -d '{\"recencia_dias\": 35}'",
    'interfaz': 'python -m ia_mlops.interfaz --url http://127.0.0.1:8080',
    'i_listo': 'curl -s http://127.0.0.1:8090/listo; echo',
    'i_salud_listo': "curl -s -w ' [%{http_code}]\\n' http://127.0.0.1:8090/salud; curl -s -w ' [%{http_code}]\\n' http://127.0.0.1:8090/listo",
}

# El fragmento de FS al vuelo: una sola orden (python lee el programa hasta EOF). Probado tal cual en local.
FS_AL_VUELO = """python - <<'EOF'
import pandas as pd
from ia_mlops import config, db, explotacion as ex
con = db.conectar(); cid = 13599; t = {}
for corte in ['2010-12-01', ex.corte_por_defecto(con)]:
    v = ex.variables_en_corte(con, corte)
    t[f'al vuelo {corte}'] = v.loc[v.cliente_id == cid, config.FEATURES].iloc[0]
fs = pd.read_sql("SELECT * FROM fs_cliente_corte WHERE cliente_id = ? AND fecha_corte = '2010-12-01'", con, params=[cid])
t['tabla fs 2010-12-01'] = fs[config.FEATURES].iloc[0]
t = pd.DataFrame(t); print(t.to_string())
a, b = t.iloc[:, 0], t.iloc[:, 2]
print('Iguales en el corte entrenado:', bool(((a == b) | (a.isna() & b.isna())).all()))
print('Cortes guardados en fs_cliente_corte:', [r[0] for r in con.execute('SELECT DISTINCT fecha_corte FROM fs_cliente_corte ORDER BY 1')])
EOF"""

# --- Salidas reales (en local, Windows, env-ia-mlops, 20/11/2026) ------------------------------------------------------------
SALIDAS = {
    'operacional': ('  OPERACIONAL: clientes               150 filas\n  OPERACIONAL: productos            3,080 filas\n'
                    '  OPERACIONAL: facturas             1,430 filas\n  OPERACIONAL: lineas_factura      23,070 filas'),
    'pipeline': ('[pipeline_ml] ejecutando (huella de entrada 16577f644dbe)\n'
                 '  FS: corte 2010-06-01: 69 clientes   …   FS: corte 2011-09-01: 131 clientes\n'
                 '  ML: train     626 filas | tasa de recompra 50.8 %\n'
                 '[pipeline_train] ejecutando (huella de entrada 7108eeb2fa32)\n'
                 '  referencia_sin_aprender    AUC valid 0.500 | test 0.500 | precision media test 0.404\n'
                 '  regresion_logistica        AUC valid 0.698 | test 0.747 | precision media test 0.659\n'
                 '  gradient_boosting          AUC valid 0.663 | test 0.735 | precision media test 0.648\n'
                 "Successfully registered model 'retencion-90d'.\n"
                 '  Mejor modelo: regresion_logistica. Guardado en …/models/modelo.joblib\n'
                 '  Registrado en MLflow como «retencion-90d», version 1. Para verlo: python -m ia_mlops.mlflow_ui'),
    'api': ('INFO:     Waiting for application startup.\n'
            '{"severity": "INFO", "message": "modelo cargado", "evento": "modelo_cargado", "huella_datos": "35a94deb4e04ab4a"}\n'
            'INFO:     Application startup complete.\n'
            'INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)'),
    'salud_listo': '{"estado":"ok"}\n{"estado":"listo"}',
    'modelo': ('{\n    "modelo": "regresion_logistica",\n    "objetivo": "el cliente compra al menos una vez en los siguientes 90 dias",\n'
               '    "huella_datos": "35a94deb4e04ab4a",\n    "entrenado_en": "2026-11-20T12:22:53",\n    "variables": [\n'
               '        "recencia_dias",\n        … (las 13 variables del contrato) …\n        "es_reino_unido"\n    ],\n'
               '    "filas": {\n        "train": 626,\n        "valid": 114,\n        "test": 250\n    },'),
    'predecir': '{"probabilidad":0.8278889191932138,"modelo":"regresion_logistica","huella_datos":"35a94deb4e04ab4a","advertencias":[]}',
    'lote': ('{"predicciones":[\n {"probabilidad":0.8278889191932137, … ,"advertencias":[]},\n'
             ' {"probabilidad":0.3061291959896073, … ,"advertencias":["dias_medios_entre_compras no informado: el modelo usa la mediana del entrenamiento."]}]}'),
    'p422': ('{"detail":[{"type":"missing","loc":["body","frecuencia"],"msg":"Field required", …},\n'
             '            … 12 campos que faltan …]} [422]'),
    'fs': ('                           al vuelo 2010-12-01  al vuelo 2011-12-10  tabla fs 2010-12-01\n'
           'recencia_dias                            21.00                 1.00                21.00\n'
           'frecuencia                               12.00                33.00                12.00\n'
           'monto_total                            4661.12              9811.04              4661.12\n'
           'ticket_medio                            388.43               297.30               388.43\n'
           'unidades_total                         2955.00              6248.00              2955.00\n'
           'productos_distintos                     100.00               235.00               100.00\n'
           'antiguedad_dias                         364.00               738.00               364.00\n'
           'frecuencia_90d                            6.00                13.00                 6.00\n'
           'monto_90d                              1752.00              2836.08              1752.00\n'
           'frecuencia_180d                           6.00                14.00                 6.00\n'
           'dias_medios_entre_compras                31.20                23.00                31.20\n'
           'devoluciones                              7.00                19.00                 7.00\n'
           'es_reino_unido                            1.00                 1.00                 1.00\n'
           'Iguales en el corte entrenado: True\n'
           "Cortes guardados en fs_cliente_corte: ['2010-06-01', '2010-07-01', '2010-08-01', '2010-09-01', '2010-10-01',"
           " '2010-11-01', '2010-12-01', '2011-03-01', '2011-06-01', '2011-09-01']"),
    'interfaz': ('Interfaz en http://127.0.0.1:8090 · predicciones: http://127.0.0.1:8080\n'
                 'INFO:     Uvicorn running on http://127.0.0.1:8090 (Press CTRL+C to quit)'),
    'i_listo': '{"estado":"listo","datos":"ok","modelo":"http://127.0.0.1:8080"}',
    'c13599': ('corte 2011-12-10 · 148 clientes en el corte\n13599  probabilidad 0.9977  alta  puesto 1  decil 1  revisar\n'
               'aviso: antiguedad_dias=738 esta fuera del rango visto al entrenar [1, 364]; la prediccion no tiene respaldo ahi.'),
    'ejemplo': ('13599  0.9977  alta   puesto 1\n14859  0.7273  alta   puesto 38\n18108  0.4159  media  puesto 75\n'
                '14752  0.2249  baja   puesto 111\n13306  0.128   baja   puesto 148\n99999  no existe en MASTER'),
    'corte': ('corte 2011-03-01 · 114 clientes en el corte\n13599  probabilidad 0.9942  alta  puesto 3\n'
              'recencia_dias 53 · frecuencia 15 · monto_total 5383.1 · antiguedad_dias 454 · devoluciones 11'),
    'parada': ('{"estado":"ok"} [200]\n'
               '{"detalle":"La API del modelo en http://127.0.0.1:8080 no responde ([WinError 10061] …). ¿Está arrancada y /listo responde?"} [503]'),
}


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


def tabla(cab, filas):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


PARTES = {'A': 'Preparar', 'B': 'Inferencia (API)', 'C': 'FS al vuelo', 'D': 'Interfaz', 'E': 'Cierre'}
SLIDES = []


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    SLIDES.append(dict(parte=parte, min=minutos, titulo=titulo, notas=notas,
                       html=f'<p class="kick">{esc(kick)}</p><h1>{md(h1)}</h1>\n{cuerpo}'))


def svg_mapa():
    cajas = [('Persona', 'conoce el id', 'n'), ('Interfaz (UI)', 'puerto 8090', 'g'), ('Variables en el corte', 'SQL de FS sobre curso.db', 'n'),
             ('API del modelo', 'puerto 8080 · 13 variables', 'n'), ('Probabilidad → tramo', 'regla de negocio', 'g')]
    o = ['<defs><marker id="fm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0 L10 5 L0 10 z" fill="#1f5fa8"/></marker></defs>']
    for i, (t, s, c) in enumerate(cajas):
        x = 8 + i * 226
        o.append(f'<rect x="{x}" y="20" width="196" height="84" rx="12" class="sv-{c}"/>'
                 f'<text x="{x + 98}" y="56" class="sv-t">{esc(t)}</text><text x="{x + 98}" y="80" class="sv-s">{esc(s)}</text>')
        if i:
            o.append(f'<path d="M{x - 28} 62 L{x - 4} 62" stroke="#1f5fa8" stroke-width="2.5" fill="none" marker-end="url(#fm)"/>')
    o.append('<text x="332" y="134" class="sv-s">D · la interfaz</text>'
             '<text x="558" y="134" class="sv-s">C · FS al vuelo</text><text x="558" y="152" class="sv-s">(el mismo cálculo que al entrenar)</text>'
             '<text x="784" y="134" class="sv-s">B · inferencia</text><text x="784" y="152" class="sv-s">(/predecir · /predecir/lote)</text>')
    return f'<svg viewBox="0 0 1140 165" role="img" aria-label="Del id a la recomendación">{"".join(o)}</svg>'


# =====================================================================================================================================
def construir():
    SLIDES.clear()

    # ------------------------------------------------------------------------------------------------ A · Preparar
    slide('A', 2, 'Portada', 'S3 · Bloque 1 · Laboratorio-recap de S2', 'S2 otra vez, pero **lo haces tú**', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  <p class="sub">En 90 minutos vuelves a montar en tu Codespace lo que vimos en S2: la API que sirve el modelo, el cálculo al vuelo de las variables y la interfaz de consulta.</p>
  <div class="card"><h3>Cómo seguirla</h3>{lista([
        'Cada orden lleva **⧉**: cópiala y pégala en el terminal del Codespace.',
        'Las salidas son **reales** (en local, {}) y las capturas, de un **Codespace del curso**. Haz clic en una captura para ampliarla; **Esc** la cierra.'.format(FECHA),
        'El mismo recorrido en texto, para repetirlo solo: `laboratorio-recap-s2/guia.md`.',
        'Teclas: **← →** avanzar · **O** índice · **S** notas · **F** pantalla completa.'])}</div>
 </div>
 <div class="card"><h3>Siglas de hoy</h3>{tabla(['Sigla', 'Qué es'], [
        ['**API**', 'Interfaz de programación: el modelo atiende peticiones HTTP (Protocolo de Transferencia de Hipertexto) con JSON.'],
        ['**FS**', 'Capa de variables (*feature store*): las 13 variables de cada cliente en una fecha de corte.'],
        ['**UI**', 'Interfaz de usuario: la página web de consulta.'],
        ['**JSON**', 'Notación de objetos de JavaScript: el formato de texto de las peticiones.'],
        ['**SQL**', 'Lenguaje de consulta estructurado: el que calcula las variables.']])}</div>
</div>''',
          'Bienvenida al bloque. Hoy no hay teoría nueva: es S2 otra vez, pero cada persona lo monta en su Codespace. Tres demostraciones: inferencia con la API, cálculo al vuelo de las variables de FS e interfaz. Insista en que la guía en texto existe para quien se quede atrás: puede seguir solo y alcanzarnos. GCP no entra hoy.')

    slide('A', 4, 'El mapa', 'Lo que vamos a recorrer', 'Del **id** a la **recomendación**, en cinco piezas', f'''
<div class="card" style="padding:14px 16px">{svg_mapa()}</div>
<div class="grid3" style="margin-top:14px">
 <div class="card"><h3>La API no sabe qué es un id</h3><p>Pide las <b>13 variables</b> del contrato y devuelve una probabilidad. No lee datos de clientes.</p></div>
 <div class="card"><h3>La persona no conoce las variables</h3><p>Solo tiene el <b>id del cliente</b> y quiere saber <b>qué hacer</b> con él.</p></div>
 <div class="card"><h3>La interfaz hace de puente</h3><p>Calcula las variables con el <b>mismo SQL de FS</b> que al entrenar, llama a la API y aplica la regla de tramos.</p></div>
</div>''',
          'Este es el mapa de todo el bloque. Recórralo de izquierda a derecha. Diga en voz alta en qué parte se ve cada pieza: B la API, C el cálculo al vuelo y D la interfaz. Pregunta para el grupo: ¿por qué la API no busca ella misma las variables por id? Respuesta de S2: así la imagen del modelo no lleva datos de clientes.')

    slide('A', 2, 'Plan y terminales', 'Cómo trabajamos', 'Tres terminales y cuatro partes', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="card"><h3>Tres terminales en el Codespace</h3>{tabla(['Terminal', 'Qué corre', 'Puerto'], [
        ['**T1**', 'la API del modelo (`uvicorn`)', '8080'],
        ['**T2**', 'la interfaz de consulta', '8090'],
        ['**T3**', 'las comprobaciones (`curl`, Python)', '—']])}
  <p class="small" style="margin-top:10px">Divide el terminal con <b>Ctrl+Shift+5</b> o con el icono ◫ del panel. Todas, desde <span class="mono">04-Proyecto-Base</span> y con <span class="mono">env-ia-mlops</span> activado.</p></div>
 <div class="card"><h3>El bloque, minuto a minuto</h3>{tabla(['Parte', 'Qué', 'Min'], [
        ['**A**', 'Preparar el Codespace', '14'],
        ['**B**', 'Inferencia: API, contrato, una predicción y un lote', '29'],
        ['**C**', 'Las variables de FS, calculadas al vuelo', '17'],
        ['**D**', 'La interfaz: 13599, variables, ejemplo, corte, vivo y listo', '25'],
        ['**E**', 'Opcional con Docker y cierre', '5']])}</div>
</div>''',
          'Que todos dividan el terminal en tres ahora, antes de empezar. Así nadie para la API sin querer al lanzar la interfaz. El reloj de abajo dice el minuto planificado: el bloque va de 0:10 a 1:40 de la sesión.')

    slide('A', 6, 'Preparar el Codespace', 'A · Paso 1 · solo en un Codespace nuevo', 'Datos y modelo: **operacional** y **pipeline**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T1 · terminal del Codespace', ['# si el terminal no está ya ahí', 'ir', 'activar', 'ver', '# crea retail.db y ejecuta RAW → MASTER → FS → ML → modelo (≈ 2 min)', 'preparar'])}
  {real('pipeline', pq=True)}
 </div>
 <div class="col capcol">{cap('r01-codespace.webp', 190)}{cap('r02-pipeline.webp', 190)}</div>
</div>''',
          'Un Codespace nuevo no trae retail.db: por eso primero operacional. El pipeline ejecuta los cuatro pasos y entrena; en local tardó unos 85 segundos. Que nadie se asuste por los avisos UserWarning y WARNING de MLflow: no son errores. Lo que importa es «Mejor modelo: regresion_logistica» y la versión registrada en MLflow. Si ya lo tenían de S2, el pipeline dice «sin cambios» en cada paso y termina enseguida.')

    # ------------------------------------------------------------------------------------------------ B · Inferencia
    slide('B', 5, 'Arrancar la API', 'B · Paso 2 · terminal T1', 'La API del modelo, escuchando en el **8080**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T1 · la API (se queda ocupada: no la cierres)', ['api'])}
  {real('api', pq=True)}
  {falla(['`address already in use`: ya hay algo en el 8080 (¿un contenedor de S2?). `docker ps` y `docker rm -f <nombre>`.',
          '`modelo no cargado` en la línea JSON: falta `models/`; vuelve al paso 1.'])}
 </div>
 <div class="col capcol">{cap('r03-api-arrancada.webp', 200)}{cap('r04-puertos.webp', 170)}</div>
</div>''',
          'El proceso se queda escuchando: el terminal T1 queda ocupado, y es normal. Fíjense en la línea JSON «modelo cargado» con la huella de los datos: es el registro estructurado de S2. En la pestaña Puertos aparece el 8080 con la etiqueta «API ia-mlops (S2)»: GitHub lo reenvía de forma privada, solo para su cuenta.')

    slide('B', 5, 'Vivo, listo y modelo', 'B · Paso 3 · terminal T3', '¿Responde? ¿Está lista? ¿**Qué modelo** es?', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T3 · comprobaciones', ['salud', 'listo', 'modelo'])}
  {real('salud_listo', pq=True)}
  <div class="card"><h3>Vivo no es lo mismo que listo</h3><p><b>/salud</b>: ¿el proceso responde? <b>/listo</b>: ¿tiene el modelo cargado? Si falta el modelo, /salud da 200 y /listo 503 con el motivo.</p></div>
 </div>
 <div class="col">{real('modelo')}
  {mira(['`huella_datos`: qué datos entrenaron el modelo. Debe ser la misma en `/modelo`, en el registro y en cada predicción.',
         '`filas`: 626 de entrenamiento, 114 de validación y 250 de prueba.',
         'Tu huella puede ser otra si tus datos son otros: compárala con la de tu registro de T1.'])}</div>
</div>''',
          'Tres preguntas distintas a la API. /salud: vivo. /listo: listo. /modelo: trazabilidad, qué modelo es y con qué datos se entrenó. La huella vuelve a aparecer en cada predicción: así se puede saber qué modelo decidió qué. python -m json.tool solo da formato al JSON.')

    slide('B', 4, 'La página /docs', 'B · Paso 4 · navegador', 'El contrato, en el navegador: **/docs**', f'''
<div class="split" style="grid-template-columns:1.15fr .85fr">
 <div class="capcol">{cap('r05-docs.webp', 400)}</div>
 <div class="col">
  <div class="card"><h3>Cómo abrirla</h3>{lista(['Pestaña **Puertos** → fila **8080** → icono del globo («Abrir en el navegador»).',
        'Añade `/docs` al final de la dirección.', 'Despliega **POST /predecir** → **Try it out**: el ejemplo ya trae las 13 variables.'])}</div>
  {mira(['Los cinco puntos de acceso: `/salud`, `/listo`, `/modelo`, `/predecir`, `/predecir/lote`.',
         'En **Schemas**, `Cliente`: los 13 campos con su tipo. Es el **contrato** que sale de la firma del modelo.'])}
 </div>
</div>''',
          'FastAPI genera esta página a partir del contrato (los esquemas de Pydantic). Es la documentación viva: si cambia el contrato, cambia la página. Que prueben Try it out con el ejemplo y vean el mismo 0,8278… que con curl en el paso siguiente.')

    slide('B', 6, 'Una predicción', 'B · Paso 5 · terminal T3', 'Una predicción con `curl` y **cliente_ejemplo.json**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T3 · un cliente', ['predecir'])}
  {real('predecir')}
  <div class="card"><h3>El cuerpo de la petición</h3><p class="small"><span class="mono">tests/datos/cliente_ejemplo.json</span>: recencia 35 días, 6 compras, 1250,40 £, 410 unidades, 38 productos, 310 días de antigüedad… las 13 variables. <span class="mono">-d @archivo</span> envía el archivo tal cual.</p></div>
 </div>
 <div class="col">{cap('r06-predecir.webp', 230)}
  {mira(['`probabilidad` ≈ **0,828**: el mismo valor que en S2 (`0.8278889…`), en local y en el contenedor.',
         '`advertencias` vacía: todas las variables están dentro de lo visto al entrenar.',
         'En T1 aparece una línea JSON `POST /predecir 200` con su `id` y los milisegundos; **sin datos del cliente**.'])}</div>
</div>''',
          'El valor 0,8278889 es el mismo de S2: mismo modelo, mismos datos de entrenamiento, mismo resultado. Si a alguien le sale otro número en las últimas cifras, es normal (operaciones en coma flotante); si cambia en la segunda o tercera cifra, algo es distinto: otros datos u otro modelo. Que miren el registro de T1: cada petición deja una línea, sin las variables del cliente.')

    slide('B', 5, 'Un lote', 'B · Paso 6 · terminal T3', 'Varios clientes de una vez: **/predecir/lote**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T3 · dos clientes', ['lote'])}
  {real('lote')}
  {mira(['Dos predicciones, **en el mismo orden** que los clientes del archivo.',
         'El primero es el de antes: la misma probabilidad.',
         'El segundo tiene `dias_medios_entre_compras: null` (una sola compra): **avisa**, no rechaza.'])}
 </div>
 <div class="col">{cap('r07-lote.webp', 240)}
  <div class="card"><h3>¿Por qué un lote?</h3><p class="small">Una campaña puntúa a cientos de clientes: una sola petición (hasta <b>1000</b>) en lugar de cientos. La interfaz usa este punto de acceso.</p></div></div>
</div>''',
          'El lote acepta hasta 1000 clientes y devuelve las predicciones en el mismo orden. El segundo cliente es un caso real: con una sola compra no hay días medios entre compras. La API no falla: usa la mediana del entrenamiento y lo dice en advertencias. Rechazar frente a avisar: rechaza lo que rompe el contrato y avisa de lo que es válido pero raro.')

    slide('B', 4, 'Romper el contrato', 'B · Paso 7 · terminal T3', 'Si falta una variable: **422**, y dice cuál', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T3 · una petición con una sola variable', ['p422'])}
  {real('p422')}
 </div>
 <div class="col">
  <div class="card"><h3>Los códigos de S2</h3>{tabla(['Código', 'Significa', 'Quién se equivocó'], [
        ['**200**', 'bien', 'nadie'], ['**422**', 'el cuerpo no cumple el contrato', 'quien llama'],
        ['**503**', 'ahora no puedo (sin modelo)', 'el servicio, y lo explica'], ['**500**', 'error interno, sin detalles', 'el servicio']])}</div>
  <div class="card"><p class="small">La API no adivina: con una sola variable devuelve la lista de las <b>12 que faltan</b> (<span class="mono">"type":"missing"</span>). Prueba también a enviar un texto donde va un número.</p></div>
 </div>
</div>''',
          'Repaso rápido del contrato. Un 422 es culpa de quien llama, y el mensaje dice exactamente qué campo falta. La salida mostrada se recortó: son doce entradas, una por cada variable que falta. Si sobra tiempo, que prueben "frecuencia": "seis" y vean el tipo de error.')

    # ------------------------------------------------------------------------------------------------ C · FS al vuelo
    slide('C', 4, '¿Por qué al vuelo?', 'C · La idea', 'La capa FS guarda **cortes del pasado**; la campaña es **hoy**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Lo que hay en la base</h3><p>La tabla <span class="mono">fs_cliente_corte</span> tiene las variables de cada cliente en los <b>10 cortes</b> de entrenamiento, validación y prueba (de 2010-06-01 a 2011-09-01).</p></div>
  <div class="card"><h3>Lo que pide la campaña</h3><p>El corte de <b>hoy</b> del dato: el día siguiente a la última factura, <span class="mono">2011-12-10</span>. <b>No está guardado</b>: hay que calcularlo.</p></div>
 </div>
 <div class="col">
  <div class="card"><h3>Cómo se calcula: <span class="mono">explotacion.variables_en_corte</span></h3>{lista([
        'Ejecuta el **mismo SQL** de la capa FS: `sql/fs/02_poblar_fs.sql`.',
        'Escribe en una tabla **temporal**: la capa FS del proyecto no se toca.',
        'Regla de oro: solo datos **anteriores al corte** (`fecha_factura < :corte`).',
        'Lo usan la interfaz y `python -m ia_mlops.explotacion`.'])}</div>
  <div class="callout">Mismo cálculo al entrenar y al predecir: si no, el modelo recibiría variables distintas de las que aprendió.</div>
 </div>
</div>''',
          'Esta es la idea central de la parte C. Lo que está guardado en la capa FS son los cortes con los que se entrenó y evaluó. Para usar el modelo hoy hacen falta las variables de hoy, y se calculan en el momento con el mismo SQL. La tabla temporal es un truco de SQLite: un nombre sin esquema se busca primero en temp, así el INSERT del SQL escribe en la copia temporal. Lo comprobaremos: en el corte de entrenamiento debe dar lo mismo que la tabla.')

    slide('C', 8, 'El fragmento de FS al vuelo', 'C · Paso 8 · terminal T3 (no necesita la API)', 'Las variables del **13599**, en dos cortes', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">{bloque('T3 · pega la orden entera (de python a EOF)', FS_AL_VUELO)}
  {falla(['`No existe la capa FS`: falta el pipeline (paso 1).', '`ModuleNotFoundError: ia_mlops`: no estás en `04-Proyecto-Base`.',
          'Se queda esperando con `>`: no se copió la última línea, `EOF`. Escríbela y pulsa Intro.'])}</div>
 <div class="col capcol">{cap('r08-fs-al-vuelo.webp', 380)}</div>
</div>''',
          'Que lo peguen entero: python - lee el programa hasta la línea EOF. Explique el código en tres partes: el bucle calcula las variables al vuelo en dos cortes, el del último entrenamiento (2010-12-01) y el de hoy (el día siguiente a la última factura); la consulta lee la fila guardada en la tabla FS para el corte entrenado; y al final se comparan. No necesita la API: es solo el dato.')

    slide('C', 5, 'Leer el resultado', 'C · Paso 8 · qué debes ver', 'Mismos valores en el corte entrenado; **otros** hoy', f'''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="col">{real('fs')}</div>
 <div class="col">
  {mira(['Columnas 1 y 3 **iguales**: `Iguales en el corte entrenado: True`.',
         'Hoy (2011-12-10) el 13599 lleva 33 compras y 738 días de antigüedad; en 2010-12-01, 12 y 364.',
         '`2011-12-10` **no está** entre los cortes guardados: por eso se calcula al vuelo.'])}
  <div class="card"><h3>Para pensar</h3><p class="small">El modelo vio antigüedades de <b>1 a 364 días</b>. Hoy el 13599 tiene <b>738</b>. ¿Qué dirá la API? Lo veremos en la interfaz: el aviso «revisar» (deriva, S5).</p></div>
 </div>
</div>''',
          'Lea la tabla con el grupo. La primera y la tercera columna coinciden fila a fila: el cálculo al vuelo es el mismo que el que se guardó al entrenar. La segunda columna es el cliente hoy: más compras, más gasto, y una antigüedad que el modelo nunca vio. Esto prepara el aviso «revisar» de la interfaz. Con el corte de hoy, 132 de los 148 clientes salen con advertencias (salida en local).')

    # ------------------------------------------------------------------------------------------------ D · Interfaz
    slide('D', 4, 'Arrancar la interfaz', 'D · Paso 9 · terminal T2', 'La interfaz, en el **8090**, llamando a la API', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('T2 · la interfaz (con la API en marcha en T1)', ['interfaz'])}
  {real('interfaz', pq=True)}
  {term('T3 · ¿está lista?', ['i_listo'])}
  {real('i_listo', pq=True)}
 </div>
 <div class="col">
  <div class="card"><h3>Abrir la página</h3>{lista(['Pestaña **Puertos** → fila **8090** («Interfaz de consulta (S2)») → icono del globo.',
        'Debajo del formulario: «predicciones: **http://127.0.0.1:8080**».'])}</div>
  {falla(['`/listo` 503 «no responde»: la API de T1 no está en marcha.', 'No sale el 8090 en Puertos: pulsa **Reenviar un puerto** y escribe 8090.'])}
 </div>
</div>''',
          'Segundo servicio: la interfaz es servidor para el navegador y cliente de la API. Su /listo comprueba las dos cosas que necesita: la base con MASTER y FS, y que la API responda a /listo. Que abran la página desde Puertos.')

    slide('D', 6, 'Consultar el 13599', 'D · Paso 10 · navegador', 'Un id → probabilidad, tramo y **las 13 variables**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col capcol">{cap('r09-interfaz-13599.webp', 230)}{cap('r10-interfaz-variables.webp', 230)}</div>
 <div class="col">
  <div class="card"><h3>Haz esto</h3>{lista(['Escribe `13599` en **Ids de cliente** y pulsa **Predecir** (la primera vez tarda unos segundos: puntúa a los 148).',
        'En su fila, despliega **Variables**.'])}</div>
  {real('c13599')}
  {mira(['**99,8 %**, tramo `alta`, puesto **1 de 148**.', 'Las variables son la columna `2011-12-10` del paso 8: recencia 1, frecuencia 33, antigüedad 738.',
         '«Revisar»: la antigüedad está fuera de lo visto al entrenar.'])}
 </div>
</div>''',
          'Conecte con la parte C: las variables que enseña la interfaz son exactamente las que calculamos a mano en el paso 8 para el corte de hoy. La interfaz no hace magia: variables_en_corte, después /predecir/lote y después la regla de tramos. Puesto y decil son entre los 148 clientes del corte.')

    slide('D', 5, 'El botón Ejemplo', 'D · Paso 11 · navegador', '**Ejemplo**: los tres tramos y un id que no existe', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col capcol">{cap('r11-interfaz-ejemplo.webp', 400)}</div>
 <div class="col">
  <div class="card"><h3>Haz esto</h3><p>Pulsa <b>Ejemplo</b> (rellena cinco ids repartidos por el ranking y el <span class="mono">99999</span>) y después <b>Predecir</b>.</p></div>
  {real('ejemplo')}
  <div class="card"><h3>La regla de negocio</h3>{tabla(['Tramo', 'Desde', 'Qué hacer'], [
        ['alta', '70 %', 'no gastar el incentivo'], ['media', '40 %', 'prioridad de la campaña'], ['baja', '0 %', 'contacto de bajo coste']])}
  <p class="small" style="margin-top:6px">En <span class="mono">config.SEGMENTOS_RECOMPRA</span>: no sale del modelo, se acuerda con negocio.</p></div>
 </div>
</div>''',
          'Ejemplo elige el primero, el último y tres intermedios del ranking, más un id inventado. Así se ven los tres tramos y el caso «sin predicción». Pregunte: ¿a quién va el incentivo? Al tramo medio, el indeciso. Los umbrales son una decisión de negocio en config.py, no del modelo.')

    slide('D', 5, 'Cambiar la fecha de corte', 'D · Paso 12 · navegador', 'Otra **fecha de corte**, otras variables', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col capcol">{cap('r12-interfaz-corte.webp', 400)}</div>
 <div class="col">
  <div class="card"><h3>Haz esto</h3><p><b>Limpiar</b>, escribe <span class="mono">13599</span>, pon <b>Fecha de corte</b> = 01/03/2011 y pulsa <b>Predecir</b>.</p></div>
  {real('corte')}
  {mira(['Solo **114** clientes en el corte: los que habían comprado antes del 1/3/2011.',
         'El 13599 baja al puesto **3**: con 15 compras y 53 días sin comprar.',
         'Es el corte de **validación**: está guardado en FS, y el cálculo al vuelo da lo mismo.'])}
 </div>
</div>''',
          'Pregunta para el grupo: ¿por qué cambian las variables? Porque todas se calculan con lo anterior al corte: en marzo de 2011 el cliente tenía menos historia. Y hay menos clientes en el corte. La interfaz acepta cortes entre la primera factura y el día siguiente a la última; fuera de ese tramo da 422.')

    slide('D', 5, 'Vivo frente a listo', 'D · Paso 13 · T1 y T3', 'Para la API: la interfaz sigue **viva**, pero no **lista**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Haz esto</h3><p>En <b>T1</b>, <b>Ctrl+C</b>: se para la API. Después, en T3:</p></div>
  {term('T3 · la interfaz con la API parada', ['i_salud_listo'])}
  {real('parada')}
  <p class="small">En Linux (Codespace) el motivo es del tipo <span class="mono">[Errno 111] Connection refused</span>.</p>
 </div>
 <div class="col">{cap('r13-listo-503.webp', 250)}
  <div class="card"><h3>Por qué importa</h3><p class="small">Si el chequeo de salud mirara <span class="mono">/listo</span>, la plataforma reiniciaría la interfaz… y no arreglaría nada: lo que falta es la API. El 503 dice <b>qué</b> falta.</p></div></div>
</div>''',
          'Vivo frente a listo, la idea de operación de S2. Reiniciar la interfaz no sirve: la API es la que falta. Al terminar, que vuelvan a arrancar la API en T1 si quieren seguir probando, o que paren las dos con Ctrl+C.')

    # ------------------------------------------------------------------------------------------------ E · Cierre
    slide('E', 3, 'Opcional: dos contenedores', 'E · Opcional · para casa', 'Lo mismo en **dos contenedores** (Docker)', '''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="card"><h3>Qué cambia</h3>''' + tabla(['', 'Hoy (procesos)', 'Contenedores (S2, parte B)'], [
        ['La interfaz llama a', '`http://127.0.0.1:8080`', '`http://api:8080` (por nombre, en una red)'],
        ['Los datos', 'tu carpeta', 'volumen de **solo lectura**'],
        ['La API', 'en el 8080 del Codespace', 'sin `-p`: no se publica']]) + '''</div>
 <div class="card"><h3>Dónde está</h3>''' + lista([
        'Recorrido: `01-Sesiones/S2-API-y-Docker/practica/interfaz-de-consulta.md`, parte B.',
        'Con Compose: `docker compose -f deploy/docker/compose.yaml up --build -d`.',
        'Antes, **para T1 y T2** (liberan el 8080 y el 8090).',
        '**Los números deben ser los mismos**: solo cambia dónde corren las piezas.']) + '''</div>
</div>''',
          'No se hace en clase: queda como opcional. Quien quiera, que siga la parte B de la práctica de S2. La única condición: parar antes la API y la interfaz de hoy para liberar los puertos. Recuerde: GCP no entra hoy; pasa a S4.')

    slide('E', 2, 'Autoevaluación y cierre', 'Cierre', 'Cuatro preguntas para llevarte', '''
<div class="grid2">
''' + ''.join(f'<div class="card"><h3>{i}. {md(p)}</h3><details><summary>Ver la respuesta</summary><p class="small">{md(r)}</p></details></div>' for i, (p, r) in enumerate([
        ('¿Por qué la API pide variables y no un id?', 'Para que la imagen del modelo no lleve datos de clientes: el dato lo pone la interfaz.'),
        ('¿Qué garantiza que las variables de hoy sean «como las de entrenar»?', 'El mismo SQL de FS (`02_poblar_fs.sql`); en el corte entrenado, el cálculo al vuelo da los mismos valores que la tabla.'),
        ('¿Qué significa «revisar» en el 13599?', 'Una variable (antigüedad 738) está fuera de lo visto al entrenar (1 a 364): la probabilidad no tiene respaldo ahí.'),
        ('API parada: ¿qué dan `/salud` y `/listo` de la interfaz?', '`/salud` 200 (vivo) y `/listo` 503 con el motivo (no lista).')], 1)) + '</div>',
          'Lea cada pregunta y deje unos segundos antes de desplegar la respuesta. Recuerde que la guía en texto queda para repetirlo en casa. Después de la pausa viene el laboratorio de GitHub Actions.')


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
pre.code{margin:0;padding:8px 12px 10px;font-family:var(--mono);font-size:12.2px;line-height:1.4;color:var(--codetx);white-space:pre-wrap;overflow-wrap:anywhere}
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
  f.innerHTML=`<span>ML e IA · S3 · Laboratorio-recap de S2</span><span><b>${esc(PARTES[s.dataset.part])}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
const hm=m=>Math.floor(m/60)+':'+String(m%60).padStart(2,'0');
let cur=0;
function go(i){i=Math.max(0,Math.min(N-1,i));cur=i;slides.forEach((s,k)=>s.classList.toggle('active',k===i));chrome();
  try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function chrome(){const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N;
  $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL+' · sesión '+hm(INICIO+cum[cur]);
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML='<p>'+esc(s.dataset.notes||'')+'</p>';
  $('#notemin').textContent='Previsto: '+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' de '+TOTAL+' (sesión '+hm(INICIO+cum[cur])+')';
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur))}
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(PARTES[s.dataset.part])} · ${s.dataset.min} min · sesión ${hm(INICIO+cum[i])}</small>${i+1}. ${esc(s.dataset.title)}</button>`).join('');
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
            '<title>Laboratorio-recap de S2 · S3 · ML e IA: de desarrollo a producción</title>\n'
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
