"""Ensayo local de la migracion: inventario, exportacion, huella, validacion y una rotura deliberada, todo medido y guardado.

ENSAYO LOCAL, NO ES GCP: no se sube nada, no hay Cloud Storage ni BigQuery. Es lo unico que se ha ejecutado de la migracion.
Todas las cifras que escribe salen de esta ejecucion; los tiempos cambian de una maquina y de una vez a otra, el resto no.
Se repite con una orden:  python -m ia_mlops.migracion ensayo --db data/processed/curso.db --salida <carpeta donde guardar>
"""
import json
import platform
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

from . import huella
from .exportar import exportar
from .fuentes import FuenteParquet, FuenteSQLite, PREFIJOS_POR_DEFECTO
from .inventario import a_texto, inventario
from .validar import validar

ROTULO = 'ENSAYO LOCAL, NO ES GCP'


def _romper_borrando_una_fila(carpeta, tabla):
    import pyarrow.parquet as pq
    ruta = Path(carpeta) / f'{tabla}.parquet'
    t = pq.read_table(ruta)
    pq.write_table(t.slice(1), ruta)


def _escribir(ruta, texto):
    Path(ruta).write_bytes((texto.rstrip('\n') + '\n').encode('utf-8'))


def ensayo(ruta_db, salida, prefijos=PREFIJOS_POR_DEFECTO, trabajo=None):
    """Ejecuta el ensayo y guarda en `salida` las salidas reales. `trabajo`: carpeta para los Parquet (por defecto, una temporal que se borra)."""
    import pyarrow
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    temporal = None if trabajo else tempfile.mkdtemp(prefix='ensayo_migracion_')
    carpeta = Path(trabajo or temporal) / 'parquet'
    roto = Path(trabajo or temporal) / 'parquet_roto'
    try:
        for c in (carpeta, roto):
            shutil.rmtree(c, ignore_errors=True)
        r = {'rotulo': ROTULO, 'entorno': {'python': sys.version.split()[0], 'pyarrow': pyarrow.__version__,
                                          'sqlite': sqlite3.sqlite_version, 'sistema': platform.system()}}
        t = time.perf_counter()
        inv = inventario(ruta_db, prefijos)
        r['inventario'] = {'segundos': round(time.perf_counter() - t, 3), 'tablas_a_migrar': len(inv['tablas_a_migrar']),
                           'tablas_no_migradas': len(inv['tablas_no_migradas']), 'bytes_sqlite': inv['bytes'],
                           'filas_total': sum(x['filas'] for x in inv['tablas_a_migrar'])}
        _escribir(salida / 'inventario.txt', f'{ROTULO}\n' + a_texto(inv))

        exp = exportar(ruta_db, carpeta, prefijos)
        r['exportar'] = {k: exp[k] for k in ('tablas', 'filas_total', 'bytes_parquet_total', 'segundos_total')}
        r['huellas_sha256'] = exp['huellas']
        lineas = [ROTULO, f'Exportadas {len(exp["tablas"])} tablas de {exp["origen"]} a Parquet en {exp["segundos_total"]} s',
                  f'{"tabla":<22}{"filas":>8}{"cols":>6}{"bytes parquet":>15}{"s":>8}']
        lineas += [f'{n:<22}{v["filas"]:>8}{v["columnas"]:>6}{v["bytes_parquet"]:>15}{v["segundos"]:>8}' for n, v in exp['tablas'].items()]
        lineas += [f'TOTAL: {exp["filas_total"]} filas, {exp["bytes_parquet_total"]} bytes de Parquet', '', 'MANIFEST.sha256 (SHA-256 de cada archivo):']
        lineas += [f'{h}  {a}' for a, h in exp['huellas'].items()]
        _escribir(salida / 'exportar.txt', '\n'.join(lineas))

        t = time.perf_counter()
        ver = huella.verificar(carpeta)
        r['verificar_huella'] = {'archivos': len(ver), 'todos_coinciden': all(v[1] for v in ver), 'segundos': round(time.perf_counter() - t, 3)}

        with FuenteSQLite(ruta_db) as origen:
            t = time.perf_counter()
            inf = validar(origen, FuenteParquet(carpeta), prefijos)
            r['validar'] = {'resultado': 'coincide' if inf.ok else 'difiere', 'comprobaciones': len(inf.comprobaciones),
                            'fallos': len(inf.fallos), 'segundos': round(time.perf_counter() - t, 3)}
            _escribir(salida / 'validar.txt', f'{ROTULO}\n' + inf.a_texto())
            t = time.perf_counter()
            inf_ex = validar(origen, FuenteParquet(carpeta), prefijos, exhaustivo=True)
            r['validar_exhaustivo'] = {'resultado': 'coincide' if inf_ex.ok else 'difiere', 'comprobaciones': len(inf_ex.comprobaciones),
                                       'segundos': round(time.perf_counter() - t, 3)}

            # Rotura deliberada: copia de la carpeta a la que se le quita UNA fila de la tabla mas grande. `validar` debe detectarlo.
            shutil.copytree(carpeta, roto)
            grande = max(exp['tablas'], key=lambda n: exp['tablas'][n]['filas'])
            _romper_borrando_una_fila(roto, grande)
            inf_roto = validar(origen, FuenteParquet(roto), prefijos)
            r['rotura_deliberada'] = {'tabla': grande, 'rotura': 'se borra una fila del Parquet', 'resultado': 'coincide' if inf_roto.ok else 'difiere',
                                      'comprobaciones_que_fallan': [f'{c.tabla}:{c.comprobacion}' for c in inf_roto.fallos]}
            _escribir(salida / 'validar-rotura.txt', f'{ROTULO}\nRotura deliberada: se borra una fila de {grande}\n' + inf_roto.a_texto())
        _escribir(salida / 'salidas-reales.json', json.dumps(r, ensure_ascii=False, indent=2))
        return r
    finally:
        if temporal:
            shutil.rmtree(temporal, ignore_errors=True)
