"""Tabla de tipos de la migracion: un TIPO LOGICO comun para comparar origen y destino.

SQLite casi no tiene tipos (cada celda guarda lo que se le da; el tipo declarado solo marca una «afinidad»), Parquet y BigQuery
si los tienen. Para poder comparar esquemas de sistemas distintos, cada fuente traduce los suyos a uno de cuatro tipos logicos y
`validar` compara SOLO tipos logicos:

    tipo logico | SQLite (tipo declarado, regla de afinidad)  | Parquet (pyarrow) | BigQuery (GoogleSQL)
    ------------+---------------------------------------------+-------------------+---------------------
    entero      | contiene «INT» (INTEGER, BIGINT...), BOOLEAN | int64             | INT64
    real        | REAL, FLOAT, DOUBLE                         | double (float64)  | FLOAT64
    texto       | CHAR, CLOB, TEXT, DATE, DATETIME, TIMESTAMP | string            | STRING
    binario     | BLOB                                        | binary            | BYTES

Decisiones (propuestas, para revisar antes de ensenar):
  * Las fechas y las horas de SQLite se guardan como TEXTO (no hay tipo fecha): se migran como texto. Convertirlas a DATE o
    TIMESTAMP en BigQuery es una decision posterior y distinta (no se hace aqui).
  * BOOLEAN de SQLite guarda 0/1: se migra como entero.
  * NUMERIC, DECIMAL y las columnas sin tipo declarado no tienen un tipo unico: el tipo se INFIERE de los valores presentes
    (todo entero -> entero; enteros y reales -> real; todo texto -> texto). Si hay una mezcla imposible, exportar falla con un mensaje.
  * La columna Parquet es siempre «anulable» y `validar` NO compara la anulabilidad (NOT NULL): compara tipos, y los nulos
    se comparan como agregado (cuantos hay en cada columna).
  * La columna de BigQuery de esta tabla sale del conocimiento general de GoogleSQL: se contrasta con la documentacion
    vigente antes de usarla en la demo real (T09). Sin verificar contra una cuenta real.
"""

ENTERO, REAL, TEXTO, BINARIO = 'entero', 'real', 'texto', 'binario'
TIPOS_LOGICOS = (ENTERO, REAL, TEXTO, BINARIO)
NUMERICOS = (ENTERO, REAL)

PARQUET = {ENTERO: 'int64', REAL: 'double', TEXTO: 'string', BINARIO: 'binary'}
BIGQUERY = {ENTERO: 'INT64', REAL: 'FLOAT64', TEXTO: 'STRING', BINARIO: 'BYTES'}

# Tipos declarados de SQLite que NO fijan un tipo logico: se infieren de los datos.
A_INFERIR = 'inferir'


def tipo_declarado_a_logico(declarado):
    """Traduce el tipo DECLARADO de una columna de SQLite a tipo logico (o A_INFERIR). Sigue las reglas de afinidad de SQLite."""
    d = (declarado or '').upper()
    if 'INT' in d or d.startswith('BOOL'):
        return ENTERO
    if any(k in d for k in ('CHAR', 'CLOB', 'TEXT', 'DATE', 'TIME')):
        return TEXTO
    if 'BLOB' in d:
        return BINARIO
    if any(k in d for k in ('REAL', 'FLOA', 'DOUB')):
        return REAL
    return A_INFERIR          # NUMERIC, DECIMAL, vacio...


def tipo_arrow_a_logico(tipo):
    """Traduce un tipo de pyarrow a tipo logico; lo que no encaja se devuelve como «otro:<tipo>» para que `validar` lo marque."""
    import pyarrow as pa
    t = pa.types
    if t.is_integer(tipo):
        return ENTERO
    if t.is_floating(tipo):
        return REAL
    if t.is_string(tipo) or t.is_large_string(tipo):
        return TEXTO
    if t.is_binary(tipo) or t.is_large_binary(tipo):
        return BINARIO
    return f'otro:{tipo}'


def logico_a_arrow(tipo):
    import pyarrow as pa
    return {ENTERO: pa.int64(), REAL: pa.float64(), TEXTO: pa.string(), BINARIO: pa.binary()}[tipo]


# BigQuery: el tipo que devuelve la API de Python (field_type, nombres «legacy») o el de GoogleSQL, hacia el tipo logico.
# Sin verificar contra una cuenta real: se contrasta en T09.
_BIGQUERY_A_LOGICO = {'INTEGER': ENTERO, 'INT64': ENTERO, 'FLOAT': REAL, 'FLOAT64': REAL, 'STRING': TEXTO, 'BYTES': BINARIO}


def tipo_bigquery_a_logico(tipo):
    """Traduce un tipo de BigQuery a tipo logico; lo que no encaja se devuelve como «otro:<tipo>» para que `validar` lo marque."""
    return _BIGQUERY_A_LOGICO.get(str(tipo).upper(), f'otro:{tipo}')