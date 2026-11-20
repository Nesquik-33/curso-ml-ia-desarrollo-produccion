# Ensayo local de la migración: **ensayo local, no es GCP**

Esto es lo ÚNICO de la migración que se ha ejecutado hasta ahora. No hay Cloud Storage, ni BigQuery, ni cuenta de nube: se exporta la base
SQLite del caso (`data/processed/curso.db`) a Parquet en una carpeta temporal del ordenador y se valida esa carpeta contra la SQLite.
Los pasos de GCP (subir, cargar en BigQuery y validar contra BigQuery) están **sin ejecutar y sin verificar**.

## Cómo se repite (desde `04-Proyecto-Base`, con el entorno del curso)
    python -m ia_mlops.migracion ensayo --db data/processed/curso.db --salida ../01-Sesiones/S3-Despliegue-y-Redes-Neuronales/practica/ensayo-local

## Qué hay aquí (todo lo escribe el programa; las cifras salen de la ejecución)
- `inventario.txt`: las 10 tablas `master_`, `fs_` y `ml_` que se migran y las 7 que no (`raw_*` y `control_pipelines`).
- `exportar.txt`: filas, columnas, bytes de Parquet y segundos por tabla, y el `MANIFEST.sha256` completo.
- `validar.txt`: la validación con la copia fiel (todo «coincide»).
- `validar-rotura.txt`: la misma validación tras borrar UNA fila de una tabla del Parquet: debe «DIFERIR» y lo hace.
- `salidas-reales.json`: todo lo anterior junto, más versiones (Python, pyarrow, SQLite) y tiempos de cada paso.
- `cli-exportar-validar.txt` (20/11/2026): las órdenes sueltas `exportar`, `huella verificar` y `validar` que usa la guía de laboratorio, con su salida real.
- `mostrar-*.txt` (20/11/2026): la salida real de cada script de `deploy/gcp/` y `deploy/cloud-run/` **sin opciones** (modo «mostrar»: imprime las órdenes y no ejecuta ninguna; sin `gcloud` en el PATH, sin `env.sh`). No es GCP.

## Qué se puede y qué no se puede decir con esto
- Se puede decir: con este ordenador y estas versiones, las 10 tablas (29743 filas) se exportaron a Parquet, la validación de conteos, esquemas,
  agregados y muestra coincide, y una rotura deliberada se detecta. Las huellas y los bytes se repiten idénticos entre ejecuciones; **los tiempos no**.
- No se puede decir: que BigQuery cargue estos Parquet con estos tipos, cuánto tarda la subida, ni nada de costes. Eso es T09 (instructor, cuenta real).
- La comparación de tipos usa tipos lógicos (entero, real, texto, binario); su equivalencia con BigQuery (INT64, FLOAT64, STRING, BYTES) está **sin verificar** con una cuenta real.
- Las huellas SHA-256 son las del origen local: Cloud Storage informa de MD5 y CRC32C, así que la integridad en la nube se comprueba descargando y volviendo a calcular.