"""Inventario: que hay en la base SQLite y que se va a migrar (fase «evaluar» de la migracion).

Lista las tablas que entran (por prefijo o por nombre) con sus filas, columnas, tipos, clave e indices, y las que NO entran con el motivo.
No cambia nada. Sirve para cualquier base SQLite, no solo la de Retail.
"""
from .fuentes import FuenteSQLite, PREFIJOS_POR_DEFECTO, seleccionar
from . import tipos


def inventario(ruta_db, prefijos=PREFIJOS_POR_DEFECTO, tablas=None):
    with FuenteSQLite(ruta_db) as f:
        todas = f.tablas()
        elegidas = seleccionar(todas, prefijos, tablas)
        a_migrar = []
        for t in elegidas:
            decl = {c[0]: c[1] for c in f.columnas_declaradas(t)}
            columnas = [{'nombre': c.nombre, 'tipo_declarado': decl[c.nombre], 'tipo_logico': c.tipo,
                         'parquet': tipos.PARQUET[c.tipo], 'bigquery': tipos.BIGQUERY[c.tipo]} for c in f.esquema(t)]
            capa = next((p for p in prefijos if t.startswith(p)), '(indicada por nombre)')
            a_migrar.append({'tabla': t, 'capa': capa, 'filas': f.filas(t), 'columnas': columnas, 'clave': f.clave(t),
                             'indices': f.indices(t)})
        no = [{'tabla': t, 'filas': f.filas(t), 'motivo': 'no empieza por un prefijo elegido' if not tablas else 'no esta en la lista indicada'}
              for t in todas if t not in elegidas]
        return {'origen': f.nombre, 'bytes': f.ruta.stat().st_size, 'prefijos': list(prefijos) if not tablas else None,
                'tablas_a_migrar': a_migrar, 'tablas_no_migradas': no, 'vistas': f.vistas()}


def a_texto(inv):
    filas = sum(t['filas'] for t in inv['tablas_a_migrar'])
    out = [f'Inventario de {inv["origen"]} ({inv["bytes"]} bytes)',
           f'Tablas a migrar: {len(inv["tablas_a_migrar"])} ({filas} filas en total)',
           f'{"tabla":<22}{"capa":<9}{"filas":>8}{"cols":>6}  clave']
    for t in inv['tablas_a_migrar']:
        out.append(f'{t["tabla"]:<22}{t["capa"]:<9}{t["filas"]:>8}{len(t["columnas"]):>6}  {", ".join(t["clave"]) or "(sin clave)"}')
    out.append(f'Tablas que NO se migran: {len(inv["tablas_no_migradas"])}')
    for t in inv['tablas_no_migradas']:
        out.append(f'  {t["tabla"]:<22}{t["filas"]:>8} filas  ({t["motivo"]})')
    if inv['vistas']:
        out.append(f'Vistas (no se migran): {", ".join(inv["vistas"])}')
    return '\n'.join(out)
