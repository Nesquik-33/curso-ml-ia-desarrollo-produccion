"""Exportar: SQLite -> una carpeta con un Parquet por tabla, mas esquema.json, conteos.json y MANIFEST.sha256.

La carpeta resultante es lo que se sube a Cloud Storage y se carga en BigQuery; tambien es el DESTINO LOCAL contra el que `validar`
ensaya la comprobacion sin nube. Necesita `pyarrow` (no esta en requirements-api.txt: la imagen del servicio no lo usa).
"""
import json
import time
from pathlib import Path

from . import huella, tipos
from .fuentes import FuenteSQLite, MigracionError, PREFIJOS_POR_DEFECTO, _q, seleccionar


def _json(v):
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    raise TypeError(type(v))


def _escribir_json(ruta, datos):
    ruta.write_bytes((json.dumps(datos, ensure_ascii=False, indent=2, default=_json) + '\n').encode('utf-8'))


def exportar_tabla(fuente, tabla, esquema, ruta, lote=50_000):
    """Escribe una tabla en Parquet por lotes y devuelve las filas escritas."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    schema = pa.schema([pa.field(c.nombre, tipos.logico_a_arrow(c.tipo)) for c in esquema])
    cursor = fuente.con.execute(f'SELECT {", ".join(_q(c.nombre) for c in esquema)} FROM {_q(tabla)}')
    escritas = 0
    with pq.ParquetWriter(ruta, schema, compression='snappy') as w:
        while True:
            filas = cursor.fetchmany(lote)
            if not filas:
                break
            arrays = []
            for c, valores in zip(esquema, zip(*filas)):
                try:
                    arrays.append(pa.array(valores, type=tipos.logico_a_arrow(c.tipo)))
                except (pa.ArrowInvalid, pa.ArrowTypeError, OverflowError) as e:
                    raise MigracionError(f'{tabla}.{c.nombre}: hay valores que no caben en {c.tipo} ({tipos.PARQUET[c.tipo]}): {e}') from e
            w.write_table(pa.Table.from_arrays(arrays, schema=schema))
            escritas += len(filas)
        if escritas == 0:
            w.write_table(schema.empty_table())
    return escritas


def exportar(ruta_db, salida, prefijos=PREFIJOS_POR_DEFECTO, tablas=None, lote=50_000):
    """Exporta las tablas elegidas. Devuelve un diccionario con filas, bytes, tiempos y huellas (todo medido, nada supuesto)."""
    try:
        import pyarrow  # noqa: F401
    except ImportError as e:
        raise MigracionError('Falta pyarrow (Parquet). Instalalo en TU entorno con: pip install pyarrow  (o usa el entorno del curso, que ya lo trae)') from e
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / huella.NOMBRE).unlink(missing_ok=True)
    t0 = time.perf_counter()
    with FuenteSQLite(ruta_db) as f:
        elegidas = seleccionar(f.tablas(), prefijos, tablas)
        if not elegidas:
            raise MigracionError(f'No hay tablas que empiecen por {tuple(prefijos)} en {f.nombre}')
        esquema_json, conteos_json, resumen = {}, {}, {}
        for t in elegidas:
            ti = time.perf_counter()
            esq = f.esquema(t)
            ruta = salida / f'{t}.parquet'
            filas = exportar_tabla(f, t, esq, ruta, lote)
            esperadas = f.filas(t)
            if filas != esperadas:
                raise MigracionError(f'{t}: se escribieron {filas} filas y la tabla tiene {esperadas}')
            agg = f.agregados(t, esq)
            declaradas = {c[0]: c[1] for c in f.columnas_declaradas(t)}
            esquema_json[t] = {'clave': f.clave(t),
                               'columnas': [{'nombre': c.nombre, 'tipo_declarado': declaradas[c.nombre], 'tipo_logico': c.tipo,
                                             'parquet': tipos.PARQUET[c.tipo], 'bigquery': tipos.BIGQUERY[c.tipo]} for c in esq]}
            conteos_json[t] = {'filas': filas, 'nulos': {k: v['nulos'] for k, v in agg.items()}, 'agregados': agg}
            resumen[t] = {'filas': filas, 'columnas': len(esq), 'bytes_parquet': ruta.stat().st_size,
                          'segundos': round(time.perf_counter() - ti, 3)}
        _escribir_json(salida / 'esquema.json', {'origen': f.nombre, 'tablas': esquema_json})
        _escribir_json(salida / 'conteos.json', {'origen': f.nombre, 'tablas': conteos_json})
        huellas = huella.generar(salida, [f'{t}.parquet' for t in elegidas] + ['esquema.json', 'conteos.json'])
        return {'origen': f.nombre, 'tablas': resumen, 'huellas': huellas, 'filas_total': sum(r['filas'] for r in resumen.values()),
                'bytes_parquet_total': sum(r['bytes_parquet'] for r in resumen.values()),
                'segundos_total': round(time.perf_counter() - t0, 3)}
