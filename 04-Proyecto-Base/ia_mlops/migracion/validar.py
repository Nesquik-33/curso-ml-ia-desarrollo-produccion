"""Validar: ¿lo que hay en el DESTINO es lo mismo que en el ORIGEN?

Compara, tabla por tabla: que exista, el esquema (nombres, orden y tipos LOGICOS), el numero de filas, los agregados por columna
(nulos, distintos, minimo, maximo y suma) y una muestra de filas (las primeras y las ultimas por clave; o todas con exhaustivo=True).
Si algo difiere, el informe lo dice y `Informe.ok` es False (la CLI sale con codigo 1).

`origen` y `destino` son FUENTES (ver fuentes.py): hoy SQLite o una carpeta de Parquet; mas adelante, BigQuery con la misma
funcion y sin tocar este archivo.

Limite honesto: agregados y muestra no prueban que CADA celda sea igual. Una alteracion que no cambie ningun agregado ni caiga en
la muestra pasaria; `exhaustivo=True` compara todas las filas (barato en local, caro en una nube con tablas grandes).
"""
import math
from dataclasses import dataclass, field

from .fuentes import PREFIJOS_POR_DEFECTO, seleccionar


@dataclass
class Comprobacion:
    tabla: str
    comprobacion: str
    ok: bool
    detalle: str


@dataclass
class Informe:
    origen: str
    destino: str
    comprobaciones: list = field(default_factory=list)

    @property
    def ok(self):
        return bool(self.comprobaciones) and all(c.ok for c in self.comprobaciones)

    @property
    def fallos(self):
        return [c for c in self.comprobaciones if not c.ok]

    def resumen(self):
        n, k = len(self.comprobaciones), len(self.fallos)
        return f'coincide ({n} comprobaciones)' if self.ok else f'DIFIERE ({k} de {n} comprobaciones fallan)'

    def a_dict(self):
        return {'origen': self.origen, 'destino': self.destino, 'resultado': 'coincide' if self.ok else 'difiere',
                'comprobaciones': [c.__dict__ for c in self.comprobaciones]}

    def a_texto(self):
        out = [f'Validacion: {self.origen} (origen) frente a {self.destino} (destino)']
        for c in self.comprobaciones:
            out.append(f'  {"coincide" if c.ok else "DIFIERE ":<9} {c.tabla:<26}{c.comprobacion:<10}{c.detalle}')
        out.append(f'RESULTADO: {self.resumen()}')
        return '\n'.join(out)


def _numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _iguales(a, b, rel=1e-12):
    if a is None or b is None:
        return a is None and b is None
    if _numero(a) and _numero(b):
        return a == b or math.isclose(a, b, rel_tol=rel, abs_tol=1e-12)
    return a == b


def _comparar_esquema(eo, ed):
    if [c.nombre for c in eo] == [c.nombre for c in ed] and [c.tipo for c in eo] == [c.tipo for c in ed]:
        return []
    no, nd = [c.nombre for c in eo], [c.nombre for c in ed]
    dif = []
    if set(no) - set(nd):
        dif.append(f'faltan en el destino: {sorted(set(no) - set(nd))}')
    if set(nd) - set(no):
        dif.append(f'sobran en el destino: {sorted(set(nd) - set(no))}')
    to, td = {c.nombre: c.tipo for c in eo}, {c.nombre: c.tipo for c in ed}
    for n in no:
        if n in td and to[n] != td[n]:
            dif.append(f'{n}: tipo {to[n]} en el origen y {td[n]} en el destino')
    if not dif:
        dif.append('mismas columnas y tipos pero en distinto orden')
    return dif


def _comparar_agregados(ao, ad, tolerancia):
    dif = []
    for col, d in ao.items():
        for k, vo in d.items():
            vd = ad[col][k]
            if not _iguales(vo, vd, tolerancia if k == 'suma' else 1e-12):
                dif.append(f'{col}.{k}: origen {vo!r}, destino {vd!r}')
    return dif


def _comparar_muestra(mo, md, columnas, clave):
    if len(mo) != len(md):
        return [f'la muestra tiene {len(mo)} filas en el origen y {len(md)} en el destino']
    dif = []
    for fo, fd in zip(mo, md):
        malas = [c for c, a, b in zip(columnas, fo, fd) if not _iguales(a, b)]
        if malas:
            llave = {c: fo[columnas.index(c)] for c in (clave or columnas[:1])}
            dif.append(f'fila {llave}: difieren {malas}')
    if len(dif) > 3:      # el informe no se llena de lineas: se ensenan las 3 primeras
        dif = dif[:3] + [f'... y {len(dif) - 3} filas mas con diferencias']
    return dif


def validar(origen, destino, prefijos=PREFIJOS_POR_DEFECTO, tablas=None, n_muestra=20, exhaustivo=False, tolerancia=1e-9,
            integridad=True):
    """Compara `origen` y `destino` (dos fuentes). Devuelve un Informe; no lanza excepciones por diferencias."""
    inf = Informe(origen.nombre, destino.nombre)
    n = None if exhaustivo else n_muestra

    def anotar(tabla, comprobacion, dif, bien):
        inf.comprobaciones.append(Comprobacion(tabla, comprobacion, not dif, bien if not dif else '; '.join(dif)))

    elegidas = seleccionar(origen.tablas(), prefijos, tablas)
    if not elegidas:
        inf.comprobaciones.append(Comprobacion('(todas)', 'tablas', False, 'el origen no tiene tablas que validar'))
        return inf
    en_destino = set(destino.tablas())
    for t in elegidas:
        if t not in en_destino:
            anotar(t, 'existe', ['la tabla no esta en el destino'], '')
            continue
        anotar(t, 'existe', [], 'esta en el destino')
        try:
            eo, ed = origen.esquema(t), destino.esquema(t)
            dif_esq = _comparar_esquema(eo, ed)
            anotar(t, 'esquema', dif_esq, f'{len(eo)} columnas, mismos nombres, orden y tipos')
            fo, fd = origen.filas(t), destino.filas(t)
            anotar(t, 'filas', [] if fo == fd else [f'origen {fo}, destino {fd}'], f'{fo} = {fd}')
            comunes = [c for c in eo if c.nombre in {x.nombre: x.tipo for x in ed} and {x.nombre: x.tipo for x in ed}[c.nombre] == c.tipo]
            ao, ad = origen.agregados(t, comunes), destino.agregados(t, comunes)
            anotar(t, 'agregados', _comparar_agregados(ao, ad, tolerancia), f'{len(comunes)} columnas: nulos, distintos, minimo, maximo, suma')
            if dif_esq:
                inf.comprobaciones.append(Comprobacion(t, 'muestra', False, 'no comparada: el esquema es distinto'))
            else:
                cols, clave = [c.nombre for c in eo], origen.clave(t)
                mo, md = origen.muestra(t, cols, clave, n), destino.muestra(t, cols, clave, n)
                anotar(t, 'muestra', _comparar_muestra(mo, md, cols, clave), f'{len(mo)} filas {"(todas)" if exhaustivo else "(primeras y ultimas por clave)"}')
        except Exception as e:      # noqa: BLE001 - un archivo corrupto es una diferencia, no un fallo del programa
            inf.comprobaciones.append(Comprobacion(t, 'lectura', False, f'error al leer: {type(e).__name__}: {e}'))
    if integridad:
        for archivo, ok, detalle in destino.integridad():
            inf.comprobaciones.append(Comprobacion(archivo, 'huella', ok, detalle))
    return inf
