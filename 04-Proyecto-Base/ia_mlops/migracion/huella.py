"""Huellas SHA-256 de una carpeta: genera y verifica un MANIFEST.sha256.

El formato es el de `sha256sum`: una linea «<huella>  <ruta relativa con />» por archivo. Asi, en una terminal con `sha256sum`,
`cd carpeta && sha256sum -c MANIFEST.sha256` hace lo mismo que `verificar` (sin verificar aqui con sha256sum de Linux).

Importante para la nube: Cloud Storage informa de MD5 y CRC32C de cada objeto, NO de SHA-256 (comprobar en la documentacion
vigente). Por eso esta huella SHA-256 es la del ORIGEN LOCAL; la integridad del objeto ya subido se comprueba DESCARGANDOLO
y volviendo a calcular su SHA-256 (o guardando la huella como metadato propio del objeto), no leyendo un campo del bucket.
"""
import hashlib
from pathlib import Path

NOMBRE = 'MANIFEST.sha256'


def sha256_archivo(ruta, bloque=1 << 20):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        while chunk := f.read(bloque):
            h.update(chunk)
    return h.hexdigest()


def generar(carpeta, archivos=None, manifiesto=None):
    """Calcula la huella de `archivos` (rutas relativas a `carpeta`; por defecto, todos menos el manifiesto) y escribe el manifiesto.

    Devuelve {ruta_relativa: huella}. El manifiesto va en la propia carpeta salvo que se indique otra ruta.
    """
    carpeta = Path(carpeta)
    manifiesto = Path(manifiesto) if manifiesto else carpeta / NOMBRE
    if archivos is None:
        archivos = [p.relative_to(carpeta).as_posix() for p in carpeta.rglob('*') if p.is_file() and p.name != NOMBRE]
    huellas = {a: sha256_archivo(carpeta / a) for a in sorted(archivos)}
    texto = ''.join(f'{h}  {a}\n' for a, h in huellas.items())
    manifiesto.write_bytes(texto.encode('utf-8'))          # bytes: el mismo \n en Windows y en Linux
    return huellas


def leer(manifiesto):
    huellas = {}
    for linea in Path(manifiesto).read_text(encoding='utf-8').splitlines():
        if not linea.strip():
            continue
        h, _, a = linea.partition(' ')
        huellas[a.lstrip(' *')] = h
    return huellas


def verificar(carpeta, manifiesto=None):
    """Recalcula las huellas y las compara con el manifiesto. Devuelve [(archivo, ok, detalle)]."""
    carpeta = Path(carpeta)
    manifiesto = Path(manifiesto) if manifiesto else carpeta / NOMBRE
    resultado = []
    for archivo, esperada in leer(manifiesto).items():
        ruta = carpeta / archivo
        if not ruta.is_file():
            resultado.append((archivo, False, 'falta el archivo'))
            continue
        real = sha256_archivo(ruta)
        resultado.append((archivo, real == esperada, 'huella igual' if real == esperada else f'huella distinta (manifiesto {esperada[:12]}..., real {real[:12]}...)'))
    return resultado
