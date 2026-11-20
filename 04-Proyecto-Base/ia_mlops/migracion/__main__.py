"""CLI de la migracion. Ejecutar desde 04-Proyecto-Base:  python -m ia_mlops.migracion <orden> --help

Codigos de salida: 0 todo coincide · 1 el destino DIFIERE del origen · 2 uso incorrecto o problema explicado (MigracionError).
"""
import argparse
import json
import sys
from pathlib import Path

from .. import config
from . import huella
from .exportar import exportar
from .fuentes import FuenteBigQuery, FuenteParquet, FuenteSQLite, MAX_BYTES_POR_DEFECTO, MigracionError, PREFIJOS_POR_DEFECTO
from .inventario import a_texto, inventario
from .validar import validar


def _lista(valor):
    return tuple(x.strip() for x in valor.split(',') if x.strip()) if valor else None


def _comunes(p):
    p.add_argument('--db', default=str(config.DB), help='SQLite de origen (por defecto, la base analitica del proyecto)')
    p.add_argument('--prefijos', default=','.join(PREFIJOS_POR_DEFECTO), help='prefijos de las tablas a migrar, separados por comas')
    p.add_argument('--tablas', default=None, help='nombres de tablas (separados por comas); sustituye a los prefijos')


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m ia_mlops.migracion', description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='orden', required=True)
    p = sub.add_parser('inventario', help='lista lo que hay y lo que se migra'); _comunes(p); p.add_argument('--json', action='store_true')
    p = sub.add_parser('exportar', help='SQLite -> Parquet + esquema.json + conteos.json + MANIFEST.sha256'); _comunes(p)
    p.add_argument('--salida', required=True, help='carpeta de destino')
    p = sub.add_parser('validar', help='compara el origen con una carpeta de Parquet'); _comunes(p)
    p.add_argument('--destino', default=None, help='carpeta con los Parquet (o use --bigquery)')
    p.add_argument('--bigquery', default=None, metavar='PROYECTO.DATASET', help='destino en BigQuery (necesita google-cloud-bigquery; sin verificar)')
    p.add_argument('--ubicacion', default=None, help='ubicacion (region) del dataset de BigQuery')
    p.add_argument('--max-bytes', type=int, default=MAX_BYTES_POR_DEFECTO, help='tope de bytes facturados por consulta en BigQuery')
    p.add_argument('--muestra', type=int, default=20, help='filas de muestra por extremo (por defecto 20)')
    p.add_argument('--exhaustivo', action='store_true', help='compara TODAS las filas')
    p.add_argument('--tolerancia', type=float, default=1e-9, help='tolerancia relativa de las sumas de reales')
    p.add_argument('--sin-huella', action='store_true', help='no verificar MANIFEST.sha256 del destino')
    p.add_argument('--json', default=None, help='guardar el informe en este archivo JSON')
    p = sub.add_parser('huella', help='genera o verifica un MANIFEST.sha256'); p.add_argument('accion', choices=['generar', 'verificar'])
    p.add_argument('carpeta')
    p = sub.add_parser('ensayo', help='ensayo local completo, medido y guardado (no es GCP)'); _comunes(p)
    p.add_argument('--salida', required=True, help='carpeta donde guardar las salidas reales')
    p.add_argument('--trabajo', default=None, help='carpeta para los Parquet (por defecto, temporal)')
    a = ap.parse_args(argv)
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, 'reconfigure'):
            flujo.reconfigure(encoding='utf-8')
    try:
        if a.orden == 'huella':
            if a.accion == 'generar':
                h = huella.generar(a.carpeta)
                print(f'{len(h)} huellas escritas en {huella.NOMBRE}')
                return 0
            res = huella.verificar(a.carpeta)
            for archivo, ok, detalle in res:
                print(f'{"coincide" if ok else "DIFIERE":<9}{archivo}: {detalle}')
            return 0 if res and all(r[1] for r in res) else 1
        prefijos, tablas = _lista(a.prefijos), _lista(a.tablas)
        if a.orden == 'inventario':
            inv = inventario(a.db, prefijos, tablas)
            print(json.dumps(inv, ensure_ascii=False, indent=2) if a.json else a_texto(inv))
            return 0
        if a.orden == 'exportar':
            r = exportar(a.db, a.salida, prefijos, tablas)
            for n, v in r['tablas'].items():
                print(f'{n:<22}{v["filas"]:>8} filas {v["bytes_parquet"]:>10} bytes')
            print(f'TOTAL {r["filas_total"]} filas, {r["bytes_parquet_total"]} bytes de Parquet, {r["segundos_total"]} s')
            return 0
        if a.orden == 'ensayo':
            from .ensayo import ensayo
            r = ensayo(a.db, a.salida, prefijos, a.trabajo)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0
        if bool(a.destino) == bool(a.bigquery):
            raise MigracionError('Indica el destino con --destino CARPETA o con --bigquery PROYECTO.DATASET (uno de los dos)')
        if a.bigquery:
            proyecto, _, dataset = a.bigquery.partition('.')
            destino = FuenteBigQuery(proyecto, dataset, a.ubicacion, a.max_bytes)
        else:
            destino = FuenteParquet(a.destino)
        with FuenteSQLite(a.db) as origen:
            inf = validar(origen, destino, prefijos, tablas, a.muestra, a.exhaustivo, a.tolerancia, not a.sin_huella)
        print(inf.a_texto())
        if a.bigquery:
            print(f'BigQuery: {destino.consultas} consultas, {destino.bytes_estimados} bytes estimados por dry run (tope por consulta: {a.max_bytes})')
        if a.json:
            Path(a.json).write_bytes((json.dumps(inf.a_dict(), ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        return 0 if inf.ok else 1
    except MigracionError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
