"""Migracion de datos de SQLite a Parquet (y, mas adelante, a BigQuery), con validacion.

    inventario  que hay y que se va a migrar            python -m ia_mlops.migracion inventario --db ...
    exportar    SQLite -> Parquet + esquema + conteos   python -m ia_mlops.migracion exportar --db ... --salida ...
    validar     origen frente a destino                 python -m ia_mlops.migracion validar --db ... --destino ...
    huella      MANIFEST.sha256 de una carpeta          python -m ia_mlops.migracion huella generar|verificar CARPETA
    ensayo      todo lo anterior, medido y guardado     python -m ia_mlops.migracion ensayo --db ... --salida ...

Parametrizado por ruta de la SQLite y por prefijos de tabla: sirve para otro caso (p. ej. Bank Marketing) sin cambiar codigo.
Todo es LOCAL: nada de esto toca la nube. Parquet necesita `pyarrow`.
"""
from .exportar import exportar
from .fuentes import FuenteBigQuery, FuenteParquet, FuenteSQLite, MigracionError, PREFIJOS_POR_DEFECTO
from .inventario import inventario
from .validar import Informe, validar


def validar_sqlite_contra_carpeta(ruta_db, carpeta, **opciones):
    """Atajo: valida una SQLite frente a la carpeta de Parquet exportada."""
    with FuenteSQLite(ruta_db) as origen:
        return validar(origen, FuenteParquet(carpeta), **opciones)


__all__ = ['exportar', 'inventario', 'validar', 'validar_sqlite_contra_carpeta', 'FuenteSQLite', 'FuenteParquet', 'FuenteBigQuery', 'Informe',
           'MigracionError', 'PREFIJOS_POR_DEFECTO']
