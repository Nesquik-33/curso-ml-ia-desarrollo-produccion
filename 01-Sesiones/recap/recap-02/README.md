# Recap 02 · S2 en 5 minutos: del modelo guardado al servicio

Se abre al empezar S3 (viernes 20/11/2026), en el primer bloque de la agenda («Recap-02 y estado del grupo», 15 minutos). Abrir `index.html` con doble clic, sin conexión.
Cómo darlo, minuto a minuto y con la versión corta de 5 minutos: [`guion-profesor.md`](guion-profesor.md).

> **Estado: preparado antes de S2; se ajusta tras el miércoles (T19).** S2 se da el miércoles 18/11/2026 y este recap se escribió el 15/11/2026, a partir de los documentos de S2 y no de lo que ocurra en el aula. Tras S2 hay que anotar lo que costó (qué diapositivas sobran o faltan, quién tiene proyecto de GCP e imagen) y corregir `index.html` y el guion. Hasta entonces, nada de lo dicho sobre S3 o GCP se ha ejecutado: es el mapa de equivalencias de la guía de S2, **sin verificar** en GCP.

## Materiales
| Archivo | Para quién | Qué es |
|---|---|---|
| `index.html` | clase | La presentación (14 diapositivas) |
| [`guion-profesor.md`](guion-profesor.md) | profesor | Ritmo, qué decir, qué preguntar, versión de 5 minutos y qué ajustar tras S2 |

## Las 14 diapositivas
| # | Diapositiva | Qué se recuerda |
|---|---|---|
| 1 | Portada | El recorrido de S2: modelo, API, imagen, contenedor y workflow |
| 2 | Un archivo no es un servicio | Lo que S2 pone alrededor del modelo guardado |
| 3 | El contrato sale de la firma | Firma, `metadatos.json` y esquema `Cliente` se comparan al arrancar; si no coinciden, 503 con el motivo |
| 4 | ¿200, 422, 503 o 500? | **Interactiva:** seis casos; quién se equivocó y por qué; rechazar frente a avisar |
| 5 | Vivo, listo y registros | `/salud` frente a `/listo`; una línea JSON por petición, con `id`, sin datos del cliente |
| 6 | La imagen Docker, capa a capa | **Interactiva:** capas, caché, versiones exactas, usuario no root, `HEALTHCHECK` y `.dockerignore` |
| 7 | Imagen, contenedor, puertos y volúmenes | Una imagen, muchos contenedores; `-p`, `-v …:ro`, `-e` |
| 8 | Un modelo, cuatro caminos, una probabilidad | `0.8278889…`, 826 MB, usuario 10001, diferencia 0 con `comparar` |
| 9 | La interfaz y los dos contenedores | Red `retencion`, API sin `-p`, volumen de solo lectura, 423 MB frente a 826 MB, roturas útiles |
| 10 | Workflow y taller | Los seis pasos de `ci.yml`; los bloques del laboratorio de S2 y el extra de punta a punta |
| 11 | Autoevaluación | Seis preguntas; **interactiva:** la respuesta aparece al pulsar |
| 12 | Puente a S3 (1) | Mapa de local a GCP: Cloud Storage, BigQuery, Secret Manager, Artifact Registry, Cloud Run, Cloud Logging |
| 13 | Puente a S3 (2) | Qué se queda igual y qué cambia; la API no lee datos; «sin verificar» |
| 14 | ¿Quién tiene…? | **Interactiva:** contadores para el diagnóstico de 5 minutos (proyecto de GCP con facturación, imagen de S2, Docker o Codespace) |

Duración: unos **11 minutos** las 13 primeras diapositivas y **4** la 14 (15 en total), como prevé la planificación de S3. Con prisa, la versión de 5 minutos del guion usa solo 1, 4, 8, 12 y 14.

## De dónde salen las cifras
Cada cifra citada existe en los documentos de S2; ninguna se ha medido de nuevo para este recap.

| Cifra | Diapositiva | Fuente |
|---|---|---|
| `0.8278889…` (valor completo `0.8278889191932133`), idéntico en local y en el contenedor | 8 | `04-Proyecto-Base/docs/api-y-contenedor.md` («Verificación») y `01-Sesiones/S2-API-y-Docker/README.md` |
| Imagen de **826 MB** en disco y 183 MB de «contenido» (GitHub Actions) | 8 y 9 | `docs/api-y-contenedor.md` («La imagen Docker») y `teoria/README.md` §10 |
| Usuario **10001** | 6, 8 y 9 | `docs/api-y-contenedor.md`, `deploy/docker/Dockerfile`, `docs/del-ordenador-al-servicio.md` §7 |
| Imagen de la interfaz de **423 MB** | 9 | `docs/del-ordenador-al-servicio.md` §5.4 (salida real de GitHub Actions, 14/11/2026) |
| Diferencia máxima **0.000e+00** con 200 filas de la muestra | 8 | `docs/api-y-contenedor.md` («Comparar los caminos») |
| 13 variables; hasta 1 000 clientes por lote | 2 y 3 | `docs/api-y-contenedor.md` («Endpoints» y «El contrato») |
| 53 paquetes en `requirements-api.lock` | 6 | `docs/api-y-contenedor.md` (tabla de decisiones) |
| Ticket medio de 5 000 libras frente a 1 295 visto al entrenar | 4 | `01-Sesiones/S2-API-y-Docker/teoria/README.md` §4 |
| Puertos 8080 (API) y 8090 (interfaz); tramos ≥ 70 %, 40–70 %, < 40 % | 7 y 9 | `docs/del-ordenador-al-servicio.md` y `docs/interfaz-de-consulta.md` |
| Bloques de 10, 25, 30, 25, 25 y 10 minutos y 135 en total (con 10 de pausa) | 10 | `01-Sesiones/S2-API-y-Docker/practica/guia-laboratorio.md` y `README.md` de S2 |
| Línea de registro de ejemplo (`id` `26ac527aa211`, 45,6 ms) | 5 | `docs/api-y-contenedor.md` («Los registros») |

No se citan cifras ni precios de GCP: las diapositivas 12 y 13 son solo el mapa de equivalencias de la guía «del ordenador al servicio» (apartado 9).

## Qué está comprobado
- Las 14 diapositivas a 1280 × 720 sin desbordes ni textos fuera de su caja, con flechas con punta y sin errores de JavaScript (Edge con Playwright, 15/11/2026). Los casos de la diapositiva 4, las capas de la 6, las preguntas de la 11 y los contadores de la 14 responden al clic; las flechas avanzan, **O** abre el índice y **S** las notas.
- El archivo es autónomo: sin imágenes ni scripts externos.

## Qué no está comprobado
- **Cómo fue S2 de verdad.** El recap se preparó antes del miércoles 18/11; el guion y las diapositivas 10 y 14 se ajustan tras la sesión (T19), con las incidencias reales y los datos de quién tiene proyecto e imagen.
- Las cifras de imagen (826 y 423 MB) son de GitHub Actions (Ubuntu), no de un Codespace del curso ni de Windows.
- Todo lo de GCP (diapositivas 12 y 13): sin ejecutar al escribir esto; marcado «sin verificar».
- **Sin hacer:** el PDF del recap (no está en `00-Planificacion/pdfs/contenido_pdfs.py`, como el de recap-01) y el enlace desde S3 y los índices (T20). No hay prueba automática guardada: recap-01 tampoco la tiene.

