"""Pruebas de la migracion SQLite -> Parquet (ia_mlops/migracion). Todo es local: no hay GCP.

Que vigilan: que `exportar` produce un Parquet por tabla con los conteos de SQLite; que `validar` PASA con la copia fiel y FALLA
(en la comprobacion esperada y solo en la de la tabla rota) cuando se borra una fila, se cambia un tipo, se altera un valor o falta
una tabla (roturas deliberadas, como las de S2); y que lo mismo sirve, sin cambiar codigo, para una SQLite de otro caso (Bank
Marketing SINTETICA: la genera esta prueba; no son los datos reales del conjunto de UCI).
Sin `pyarrow` en el entorno, TODO este archivo se omite (no falla): pyarrow no esta en requirements-api.txt.
"""
import random
import shutil
import sqlite3
import sys
from types import SimpleNamespace

import pytest

pa = pytest.importorskip('pyarrow', reason='pyarrow no esta instalado: las pruebas de migracion (Parquet) se omiten')
import pyarrow.compute as pc  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from ia_mlops import migracion as mig  # noqa: E402
from ia_mlops.migracion import huella, tipos  # noqa: E402
from ia_mlops.migracion.__main__ import main  # noqa: E402

DIEZ_TABLAS = {'master_calidad', 'master_clientes', 'master_descartes', 'master_facturas', 'master_lineas', 'master_productos',
               'fs_catalogo', 'fs_cliente_corte', 'ml_dataset', 'ml_particiones'}


# ------------------------------------------------------------------------------------------------ ayudas
def filas_sqlite(ruta, tabla):
    c = sqlite3.connect(ruta)
    try:
        return c.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]
    finally:
        c.close()


def reescribir(carpeta, tabla, cambio):
    """Abre <tabla>.parquet, le aplica `cambio(tabla_arrow) -> tabla_arrow` y lo vuelve a guardar (la rotura deliberada)."""
    ruta = carpeta / f'{tabla}.parquet'
    pq.write_table(cambio(pq.read_table(ruta)), ruta)


def fallos(informe):
    """{(tabla, comprobacion)} de lo que falla."""
    return {(c.tabla, c.comprobacion) for c in informe.fallos}


def validar_carpeta(ruta_db, carpeta, **kw):
    return mig.validar_sqlite_contra_carpeta(ruta_db, carpeta, **kw)


@pytest.fixture(scope='module')
def exportado(ruta_db, tmp_path_factory):
    carpeta = tmp_path_factory.mktemp('parquet')
    resultado = mig.exportar(ruta_db, carpeta)
    return carpeta, resultado


@pytest.fixture()
def copia(exportado, tmp_path):
    """Una copia que se puede romper sin tocar la exportacion buena."""
    destino = tmp_path / 'destino'
    shutil.copytree(exportado[0], destino)
    return destino


# ------------------------------------------------------------------------------------------------ inventario y exportacion
def test_el_inventario_lista_las_diez_tablas_y_deja_fuera_las_raw(ruta_db):
    inv = mig.inventario(ruta_db)
    assert {t['tabla'] for t in inv['tablas_a_migrar']} == DIEZ_TABLAS
    assert len(inv['tablas_a_migrar']) == 10
    assert all(t['tabla'].startswith('raw_') or t['tabla'] == 'control_pipelines' for t in inv['tablas_no_migradas'])
    for t in inv['tablas_a_migrar']:
        assert t['filas'] == filas_sqlite(ruta_db, t['tabla']) and t['clave'], t['tabla']


def test_el_inventario_respeta_prefijos_y_nombres(ruta_db):
    assert {t['tabla'] for t in mig.inventario(ruta_db, prefijos=('ml_',))['tablas_a_migrar']} == {'ml_dataset', 'ml_particiones'}
    assert [t['tabla'] for t in mig.inventario(ruta_db, tablas=['fs_catalogo'])['tablas_a_migrar']] == ['fs_catalogo']
    with pytest.raises(mig.MigracionError, match='No existen'):
        mig.inventario(ruta_db, tablas=['no_existe'])


def test_exportar_produce_un_parquet_por_tabla_con_los_conteos_de_sqlite(ruta_db, exportado):
    carpeta, r = exportado
    assert {p.stem for p in carpeta.glob('*.parquet')} == DIEZ_TABLAS
    for t in DIEZ_TABLAS:
        n = filas_sqlite(ruta_db, t)
        assert pq.ParquetFile(carpeta / f'{t}.parquet').metadata.num_rows == n == r['tablas'][t]['filas']
    assert r['filas_total'] == sum(v['filas'] for v in r['tablas'].values())
    import json
    conteos = json.loads((carpeta / 'conteos.json').read_text(encoding='utf-8'))
    assert {t: v['filas'] for t, v in conteos['tablas'].items()} == {t: v['filas'] for t, v in r['tablas'].items()}
    esquema = json.loads((carpeta / 'esquema.json').read_text(encoding='utf-8'))
    col = {c['nombre']: c for c in esquema['tablas']['fs_cliente_corte']['columnas']}
    assert (col['cliente_id']['tipo_logico'], col['monto_total']['tipo_logico'], col['fecha_corte']['tipo_logico']) == ('entero', 'real', 'texto')
    assert (col['monto_total']['parquet'], col['monto_total']['bigquery']) == ('double', 'FLOAT64')


def test_los_tipos_de_parquet_son_los_de_la_tabla_de_tipos(exportado):
    carpeta, _ = exportado
    esq = pq.read_schema(carpeta / 'fs_cliente_corte.parquet')
    assert str(esq.field('cliente_id').type) == 'int64' and str(esq.field('monto_total').type) == 'double' and str(esq.field('fecha_corte').type) == 'string'


def test_el_manifiesto_tiene_formato_sha256sum_y_se_verifica(exportado):
    carpeta, r = exportado
    lineas = (carpeta / huella.NOMBRE).read_text(encoding='utf-8').splitlines()
    assert len(lineas) == 12                      # 10 Parquet + esquema.json + conteos.json
    import re
    assert all(re.fullmatch(r'[0-9a-f]{64}  \S+', ln) for ln in lineas)
    assert dict(l.split('  ')[::-1] for l in lineas) == r['huellas']
    assert all(ok for _, ok, _ in huella.verificar(carpeta))


def test_la_exportacion_es_repetible_byte_a_byte(ruta_db, exportado, tmp_path):
    otra = tmp_path / 'otra'
    assert mig.exportar(ruta_db, otra)['huellas'] == exportado[1]['huellas']


def test_el_origen_no_se_modifica(ruta_db, tmp_path):
    antes = ruta_db.read_bytes()
    mig.exportar(ruta_db, tmp_path / 'x')
    assert ruta_db.read_bytes() == antes


def test_una_tabla_vacia_se_exporta_y_se_valida(tmp_path):
    origen = tmp_path / 'o.db'
    c = sqlite3.connect(origen)
    c.execute('CREATE TABLE master_vacia (id INTEGER PRIMARY KEY, nombre TEXT, valor REAL)')
    c.commit(); c.close()
    mig.exportar(origen, tmp_path / 'p')
    assert mig.validar_sqlite_contra_carpeta(origen, tmp_path / 'p').ok


# ------------------------------------------------------------------------------------------------ tipos
@pytest.mark.parametrize('declarado, logico', [
    ('INTEGER', 'entero'), ('BIGINT', 'entero'), ('BOOLEAN', 'entero'), ('REAL', 'real'), ('DOUBLE', 'real'), ('FLOAT', 'real'),
    ('TEXT', 'texto'), ('VARCHAR(20)', 'texto'), ('DATE', 'texto'), ('TIMESTAMP', 'texto'), ('BLOB', 'binario'),
    ('NUMERIC', 'inferir'), ('DECIMAL(10,2)', 'inferir'), ('', 'inferir')])
def test_tabla_de_tipos_de_sqlite(declarado, logico):
    assert tipos.tipo_declarado_a_logico(declarado) == logico


def test_columna_sin_tipo_se_infiere_de_los_datos_o_falla_si_hay_mezcla(tmp_path):
    o = tmp_path / 'o.db'
    c = sqlite3.connect(o)
    c.execute('CREATE TABLE master_ok (id INTEGER PRIMARY KEY, a NUMERIC, b, c NUMERIC)')
    c.executemany('INSERT INTO master_ok VALUES (?,?,?,?)', [(1, 1, 'x', 7), (2, 2.5, 'y', 8), (3, None, None, None)])
    c.execute('CREATE TABLE master_mezcla (id INTEGER PRIMARY KEY, m)')
    c.executemany('INSERT INTO master_mezcla VALUES (?,?)', [(1, 1), (2, 'dos')])
    c.commit(); c.close()
    with mig.FuenteSQLite(o) as f:
        assert {x.nombre: x.tipo for x in f.esquema('master_ok')} == {'id': 'entero', 'a': 'real', 'b': 'texto', 'c': 'entero'}
        with pytest.raises(mig.MigracionError, match='mezcla'):
            f.esquema('master_mezcla')
    with pytest.raises(mig.MigracionError, match='mezcla'):
        mig.exportar(o, tmp_path / 'p')

def test_un_valor_que_no_cabe_en_su_tipo_declarado_falla_con_mensaje(tmp_path):
    o = tmp_path / 'o.db'
    c = sqlite3.connect(o)
    c.execute('CREATE TABLE master_t (id INTEGER PRIMARY KEY, n INTEGER)')
    c.executemany('INSERT INTO master_t VALUES (?,?)', [(1, 5), (2, 'no es un numero')])
    c.commit(); c.close()
    with pytest.raises(mig.MigracionError, match=r'master_t\.n'):
        mig.exportar(o, tmp_path / 'p')


def test_sin_pyarrow_exportar_lo_explica_y_no_se_cae(ruta_db, tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, 'pyarrow', None)           # simula un entorno sin pyarrow
    with pytest.raises(mig.MigracionError, match='pyarrow'):
        mig.exportar(ruta_db, tmp_path / 'x')


# ------------------------------------------------------------------------------------------------ validar: la copia fiel
def test_validar_pasa_con_la_copia_fiel(ruta_db, exportado):
    inf = validar_carpeta(ruta_db, exportado[0])
    assert inf.ok, inf.a_texto()
    por_tabla = {(c.tabla, c.comprobacion) for c in inf.comprobaciones}
    assert all((t, k) in por_tabla for t in DIEZ_TABLAS for k in ('existe', 'esquema', 'filas', 'agregados', 'muestra'))
    assert inf.resumen().startswith('coincide')


def test_validar_exhaustivo_pasa_con_la_copia_fiel(ruta_db, exportado):
    assert validar_carpeta(ruta_db, exportado[0], exhaustivo=True).ok


def test_el_informe_se_serializa_y_dice_el_resultado(ruta_db, exportado):
    d = validar_carpeta(ruta_db, exportado[0]).a_dict()
    assert d['resultado'] == 'coincide' and len(d['comprobaciones']) > 50
    assert 'RESULTADO: coincide' in validar_carpeta(ruta_db, exportado[0]).a_texto()


# ------------------------------------------------------------------------------------------------ validar: roturas deliberadas
def test_rotura_borrar_una_fila_se_detecta(ruta_db, copia):
    reescribir(copia, 'ml_dataset', lambda t: pa.concat_tables([t.slice(0, 400), t.slice(401)]))
    inf = validar_carpeta(ruta_db, copia)
    assert not inf.ok
    assert ('ml_dataset', 'filas') in fallos(inf) and ('ml_dataset', 'agregados') in fallos(inf)
    assert {t for t, _ in fallos(inf) if t in DIEZ_TABLAS} == {'ml_dataset'}, 'solo la tabla rota debe fallar'
    detalle = next(c.detalle for c in inf.fallos if c.comprobacion == 'filas')
    assert '990' in detalle and '989' in detalle


def test_rotura_cambiar_un_tipo_se_detecta(ruta_db, copia):
    def a_texto(t):
        i = t.schema.get_field_index('frecuencia')
        return t.set_column(i, 'frecuencia', pc.cast(t.column('frecuencia'), pa.string()))
    reescribir(copia, 'fs_cliente_corte', a_texto)
    inf = validar_carpeta(ruta_db, copia)
    assert ('fs_cliente_corte', 'esquema') in fallos(inf)
    assert ('fs_cliente_corte', 'muestra') in fallos(inf)          # no se compara la muestra con otro esquema
    assert {t for t, _ in fallos(inf) if t in DIEZ_TABLAS} == {'fs_cliente_corte'}
    assert 'frecuencia: tipo entero en el origen y texto en el destino' in next(c.detalle for c in inf.fallos if c.comprobacion == 'esquema')


def test_rotura_cambiar_entero_por_real_tambien_se_detecta(ruta_db, copia):
    reescribir(copia, 'ml_dataset', lambda t: t.set_column(t.schema.get_field_index('y'), 'y', pc.cast(t.column('y'), pa.float64())))
    assert ('ml_dataset', 'esquema') in fallos(validar_carpeta(ruta_db, copia))


def test_rotura_alterar_un_valor_se_detecta(ruta_db, copia):
    def alterar(t):
        i = t.schema.get_field_index('monto_total')
        v = t.column('monto_total').to_pylist()
        v[500] = v[500] + 1.0
        return t.set_column(i, 'monto_total', pa.array(v, type=pa.float64()))
    reescribir(copia, 'fs_cliente_corte', alterar)
    inf = validar_carpeta(ruta_db, copia)
    assert ('fs_cliente_corte', 'agregados') in fallos(inf)
    assert 'monto_total.suma' in next(c.detalle for c in inf.fallos if c.comprobacion == 'agregados')
    assert {t for t, _ in fallos(inf) if t in DIEZ_TABLAS} == {'fs_cliente_corte'}


def test_rotura_que_no_cambia_ningun_agregado_solo_la_ve_el_modo_exhaustivo(ruta_db, copia):
    """Se intercambian dos valores del MEDIO de la columna: misma suma, minimo, maximo y distintos, y fuera de la muestra (limite honesto)."""
    def intercambiar(t):
        v = t.column('frecuencia').to_pylist()
        a = 400
        b = next(i for i in range(450, 600) if v[i] != v[a])
        v[a], v[b] = v[b], v[a]
        return t.set_column(t.schema.get_field_index('frecuencia'), 'frecuencia', pa.array(v, type=pa.int64()))
    reescribir(copia, 'fs_cliente_corte', intercambiar)
    normal = validar_carpeta(ruta_db, copia, integridad=False)
    assert ('fs_cliente_corte', 'agregados') not in fallos(normal) and ('fs_cliente_corte', 'muestra') not in fallos(normal)
    assert ('fs_cliente_corte', 'muestra') in fallos(validar_carpeta(ruta_db, copia, exhaustivo=True, integridad=False))
    assert ('fs_cliente_corte.parquet', 'huella') in fallos(validar_carpeta(ruta_db, copia)), 'la huella tambien lo ve'


def test_rotura_quitar_una_tabla_se_detecta(ruta_db, copia):
    (copia / 'ml_particiones.parquet').unlink()
    inf = validar_carpeta(ruta_db, copia)
    assert ('ml_particiones', 'existe') in fallos(inf)
    assert {t for t, k in fallos(inf) if t in DIEZ_TABLAS} == {'ml_particiones'}
    assert ('ml_particiones.parquet', 'huella') in fallos(inf)


def test_rotura_un_archivo_corrupto_se_detecta_sin_romper_la_validacion(ruta_db, copia):
    ruta = copia / 'ml_dataset.parquet'
    ruta.write_bytes(ruta.read_bytes()[:200])
    inf = validar_carpeta(ruta_db, copia)
    assert not inf.ok and {t for t, _ in fallos(inf) if t in DIEZ_TABLAS} == {'ml_dataset'}


def test_rotura_una_columna_menos_y_otra_de_mas(ruta_db, copia):
    reescribir(copia, 'ml_particiones', lambda t: t.drop([t.column_names[-1]]).append_column('sobrante', pa.array([1] * t.num_rows)))
    d = next(c.detalle for c in validar_carpeta(ruta_db, copia).fallos if c.comprobacion == 'esquema')
    assert 'faltan en el destino' in d and 'sobran en el destino' in d


def test_las_tablas_de_mas_en_el_destino_no_son_un_fallo(ruta_db, copia):
    shutil.copy(copia / 'ml_particiones.parquet', copia / 'otra_tabla.parquet')
    assert validar_carpeta(ruta_db, copia, integridad=False).ok


# ------------------------------------------------------------------------------------------------ la CLI y sus codigos de salida
def test_cli_codigos_de_salida(ruta_db, exportado, copia, capsys):
    base = ['validar', '--db', str(ruta_db)]
    assert main(base + ['--destino', str(exportado[0])]) == 0
    assert 'RESULTADO: coincide' in capsys.readouterr().out
    (copia / 'ml_particiones.parquet').unlink()
    assert main(base + ['--destino', str(copia)]) == 1
    assert 'RESULTADO: DIFIERE' in capsys.readouterr().out
    assert main(base + ['--destino', str(copia / 'no_existe')]) == 2
    assert main(['validar', '--db', str(copia / 'no.db'), '--destino', str(copia)]) == 2


def test_cli_inventario_exportar_y_huella(ruta_db, tmp_path, capsys):
    assert main(['inventario', '--db', str(ruta_db)]) == 0
    assert 'Tablas a migrar: 10' in capsys.readouterr().out
    salida = tmp_path / 'p'
    assert main(['exportar', '--db', str(ruta_db), '--salida', str(salida), '--prefijos', 'ml_']) == 0
    assert {p.stem for p in salida.glob('*.parquet')} == {'ml_dataset', 'ml_particiones'}
    assert main(['huella', 'verificar', str(salida)]) == 0
    (salida / 'ml_dataset.parquet').write_bytes(b'otra cosa')
    assert main(['huella', 'verificar', str(salida)]) == 1


# ------------------------------------------------------------------------------------------------ otro caso: Bank Marketing (sintetico)
def crear_bank_marketing(ruta, n=300, semilla=7):
    """SQLite sintetica con la forma de un caso de marketing bancario. NO son los datos reales de UCI: valores inventados por semilla."""
    rng = random.Random(semilla)
    trabajos, civil = ['admin.', 'obrero', 'tecnico', 'servicios', 'jubilado'], ['casado', 'soltero', 'divorciado']
    c = sqlite3.connect(ruta)
    c.executescript('''
        CREATE TABLE master_clientes (cliente_id INTEGER PRIMARY KEY, edad INTEGER, trabajo TEXT, estado_civil TEXT, saldo REAL,
                                      vivienda BOOLEAN, puntuacion NUMERIC, alta DATE);
        CREATE TABLE master_notas (nota_id INTEGER PRIMARY KEY, texto TEXT);
        CREATE TABLE fs_contactos (cliente_id INTEGER, mes TEXT, duracion_s INTEGER, campana INTEGER, dias_previos INTEGER,
                                   resultado_previo TEXT, PRIMARY KEY (cliente_id, mes));
        CREATE TABLE ml_dataset (cliente_id INTEGER PRIMARY KEY, edad INTEGER, saldo REAL, duracion_s INTEGER, y TEXT);
        CREATE TABLE raw_ficheros (id INTEGER PRIMARY KEY, nombre TEXT);
    ''')
    for i in range(1, n + 1):
        edad, saldo = rng.randint(18, 90), round(rng.gauss(1400, 3000), 2)
        c.execute('INSERT INTO master_clientes VALUES (?,?,?,?,?,?,?,?)',
                  (i, edad, rng.choice(trabajos), rng.choice(civil), saldo, rng.randint(0, 1),
                   rng.choice([1, 2, 3.5, None]), f'2020-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}'))
        dur = rng.randint(5, 900)
        for mes in rng.sample(['ene', 'feb', 'mar', 'abr'], 2):
            c.execute('INSERT INTO fs_contactos VALUES (?,?,?,?,?,?)',
                      (i, mes, dur, rng.randint(1, 6), rng.choice([None, rng.randint(1, 400)]), rng.choice([None, 'exito', 'fracaso'])))
        c.execute('INSERT INTO ml_dataset VALUES (?,?,?,?,?)', (i, edad, saldo, dur, rng.choice(['yes', 'no'])))
    c.execute("INSERT INTO raw_ficheros VALUES (1, 'bank.csv')")
    c.commit(); c.close()
    return ruta


@pytest.fixture(scope='module')
def bank(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp('bank')
    ruta = crear_bank_marketing(carpeta / 'bank.db')
    mig.exportar(ruta, carpeta / 'parquet')
    return ruta, carpeta / 'parquet'


def test_otro_caso_inventario_exportacion_y_validacion_sin_cambiar_codigo(bank):
    ruta, parquet = bank
    inv = mig.inventario(ruta)
    assert {t['tabla'] for t in inv['tablas_a_migrar']} == {'master_clientes', 'master_notas', 'fs_contactos', 'ml_dataset'}
    assert [t['tabla'] for t in inv['tablas_no_migradas']] == ['raw_ficheros']
    assert {t['tabla']: t['filas'] for t in inv['tablas_a_migrar']}['fs_contactos'] == 600
    inf = validar_carpeta(ruta, parquet, exhaustivo=True)
    assert inf.ok, inf.a_texto()


def test_otro_caso_tipos_nulos_y_clave_compuesta(bank):
    ruta, parquet = bank
    esq = {c['nombre']: c['tipo_logico'] for t in mig.inventario(ruta)['tablas_a_migrar'] if t['tabla'] == 'master_clientes' for c in t['columnas']}
    assert esq['vivienda'] == 'entero' and esq['alta'] == 'texto' and esq['puntuacion'] == 'real'
    with mig.FuenteSQLite(ruta) as f:
        assert f.clave('fs_contactos') == ['cliente_id', 'mes']
        assert f.agregados('fs_contactos', f.esquema('fs_contactos'))['dias_previos']['nulos'] > 0
    assert pq.read_table(parquet / 'fs_contactos.parquet').column('resultado_previo').null_count > 0


def test_otro_caso_las_roturas_tambien_se_detectan(bank, tmp_path):
    ruta, parquet = bank
    rota = tmp_path / 'rota'
    shutil.copytree(parquet, rota)
    reescribir(rota, 'ml_dataset', lambda t: t.slice(1))
    assert {('ml_dataset', 'filas'), ('ml_dataset', 'agregados')} <= fallos(validar_carpeta(ruta, rota))
    (rota / 'master_notas.parquet').unlink()
    assert ('master_notas', 'existe') in fallos(validar_carpeta(ruta, rota))


def test_otro_caso_se_puede_cambiar_el_prefijo(bank, tmp_path):
    ruta, _ = bank
    c = sqlite3.connect(ruta.parent / 'bank2.db')
    c.execute('CREATE TABLE bm_clientes (id INTEGER PRIMARY KEY, edad INTEGER)')
    c.executemany('INSERT INTO bm_clientes VALUES (?,?)', [(i, 20 + i) for i in range(10)])
    c.commit(); c.close()
    mig.exportar(ruta.parent / 'bank2.db', tmp_path / 'p', prefijos=('bm_',))
    assert validar_carpeta(ruta.parent / 'bank2.db', tmp_path / 'p', prefijos=('bm_',)).ok


# ------------------------------------------------------------------------------------------------ la marca «gcp»
def test_la_marca_gcp_esta_registrada_y_se_omite_por_defecto():
    import conftest
    marca = SimpleNamespace(nombre=None)
    anadidas = []

    def item(con_marca):
        return SimpleNamespace(get_closest_marker=lambda n: marca if (con_marca and n == 'gcp') else None, add_marker=anadidas.append)
    conftest.omitir_gcp([item(True), item(False)], entorno={})
    assert len(anadidas) == 1 and 'GCP' in anadidas[0].kwargs['reason']
    anadidas.clear()
    conftest.omitir_gcp([item(True)], entorno={'CURSO_PRUEBAS_GCP': '1'})
    assert anadidas == []
    import tomllib
    cfg = tomllib.loads((conftest.RAIZ / 'pyproject.toml').read_text(encoding='utf-8'))
    assert any(m.startswith('gcp:') for m in cfg['tool']['pytest']['ini_options']['markers'])
