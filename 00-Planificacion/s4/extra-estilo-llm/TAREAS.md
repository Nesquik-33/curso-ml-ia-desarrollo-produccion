# Tareas · Extra de S4: LLM de visión que copia el estilo de color

Plan: [`PLANIFICACION.md`](PLANIFICACION.md). Estado: **borrador del 20/11/2026**; las tareas T02 en adelante se lanzan **después** del veredicto del pico (T00).

**Marcas.** **[PICO]** = depende de las cifras del estudio técnico. **[D n]** = depende de la decisión n del §10 de la planificación.
**Modelo:** **Haiku** para lo mecánico con una regla clara (requisitos, pruebas estáticas, índice, comprobaciones de rutas y licencias); **Sonnet** para diseño, código, notebooks y redacción didáctica. **Opus** solo para la revisión final si el instructor lo pide.
**Prioridad:** P1 = imprescindible para publicar el extra · P2 = deseable · P3 = opcional.

| # | Tarea | Entregables | Prueba de aceptación | Depende de | Modelo | Prior. |
|---|---|---|---|---|---|---|
| T00 | **Estudio técnico (pico)** — en curso | `00-Planificacion/s4/_pico_llm_estilo/` (4 notebooks ejecutados, `INFORME.md`, paneles) | Veredicto escrito; cada cifra con su celda de origen; licencias anotadas | — | Opus (en curso) | P1 |
| T01 | Revisión del veredicto con el instructor | Respuestas a D1–D4; elección de modelo, resolución, nº de ejemplos y qué va en vivo | Anotado en la planificación con fecha | T00 | instructor | P1 |
| T02 | Esqueleto del extra | Carpeta `01-Sesiones/S4-…/extra-estilo-llm/` [D1] con `README.md` (borrador), `img/`, `pruebas/`, `estilo/__init__.py`; `.gitignore` para datos y modelos | Las carpetas existen; nada pesado dentro | T01 | Haiku | P1 |
| T03 | Requisitos fijados | `requisitos-extra-estilo.txt` con las versiones del pico (torch CPU con su índice, transformers, peft, accelerate, scikit-image, mlflow 3.18, jupyter, matplotlib) | Coincide con el `INFORME.md`; se instala en un venv limpio (anotar tiempo real) | T00 T02 | Haiku | P1 |
| T04 | Módulo compartido `estilo/` | `ajustes.py` (aplicar JSON a una foto, rangos, semilla), `metricas.py` (error por parámetro, ΔE/histograma, SSIM), `reinhard.py`, `vlm.py` (cargar el modelo y el adaptador, prompt, parsear JSON) — código sacado del pico, limpio y comentado para alumnos | Pruebas de T05 en verde; mismas cifras que el pico en una muestra | T00 T02 | Sonnet | P1 |
| T05 | Pruebas sin modelos | `pruebas/test_extra.py`: aplicar el JSON a la original reproduce la editada; SSIM(imagen, imagen) = 1; Reinhard idempotente consigo misma; parsear JSON válido/ inválido; rutas relativas | `pytest -q` en verde en < 10 s y sin red | T04 | Haiku | P1 |
| T06 | Notebook 00 · preparar entorno | `00_preparar_entorno.ipynb`: versiones, descarga del VLM y de las fotos a una caché fuera del repo, memoria e hilos, «si falla» (proxy, espacio, memoria) | Ejecutado con salidas; sin rutas personales | T03 T04 | Sonnet | P1 |
| T07 | Notebook 01 · datos fabricados | `01_datos_fabricados.ipynb` con texto didáctico (por qué fabricar datos), la tabla de ajustes, antes/después de 6 fotos, reparto con semilla, guardar parejas | Ejecutado; las parejas cumplen la prueba de T05; imágenes en `img/` | T04 T06 | Sonnet | P1 |
| T08 | Notebook 02 · zero-shot | `02_zero_shot.ipynb`: qué es un VLM, el prompt, respuestas reales (buenas y malas), % JSON válido, error por parámetro | Ejecutado; cifras = pico (o se explica la diferencia) | T07 | Sonnet | P1 |
| T09 | Notebook 03 · fine-tuning LoRA | `03_fine_tuning_lora.ipynb`: qué es LoRA (dibujo simple), configuración, curva de pérdida, error en test, tiempo, tamaño del adaptador, registro en MLflow (base del extra, no la del proyecto) | Ejecutado (o preentrenado según T01, y entonces se dice); adaptador cargable | T07 T01 | Sonnet | P1 |
| T10 | Notebook 04 · comparar y transferir | `04_comparar_y_transferir.ipynb`: C (red pequeña) y D (Reinhard), tabla A/B/C/D, panel de 3–4 parejas, conclusión «¿hacía falta un LLM?» | Ejecutado; tabla = pico; panel revisado a ojo | T08 T09 | Sonnet | P1 |
| T11 | README del extra | Qué es, para quién, requisitos, cómo seguirlo con y sin ejecutar, tiempos reales, licencias y citas (Oxford-IIIT Pet CC BY-SA 4.0; licencia del VLM; pesos de torchvision «sin verificar» si sigue así) | Cada cifra con origen; enlaces relativos que resuelven | T06–T10 | Sonnet | P1 |
| T12 | Revisión didáctica | Lectura completa como alumno: términos sin explicar, saltos, celdas largas, cifras sin origen; lista de cambios aplicada | Lista de hallazgos cerrada | T06–T11 | Sonnet | P1 |
| T13 | Comprobaciones mecánicas | Búsqueda de rutas personales, correos, tokens y nombres de usuario en notebooks (también en las salidas); tamaño total de la carpeta; imágenes citadas existen | Informe vacío de hallazgos; carpeta < [fijar tras el pico] MB | T12 | Haiku | P1 |
| T14 | Índice de S4 | Alta del extra en `00-Planificacion/indices-de-sesion/contenido_indices.py` (S4) y regenerar | `test_indice.py` en verde | T11 | Haiku | P2 |
| T15 | Notebook 05 · prueba tu foto | `05_prueba_tu_foto.ipynb`: dos fotos propias → resultado; sin guardar fotos del alumno | Ejecutado con fotos de ejemplo con licencia | T10 | Sonnet | P3 |
| T16 | CI de pruebas rápidas | Job inicial del workflow que ejecuta `pruebas/test_extra.py` (sin modelos) | Run real en verde (enlace) | T05 | Haiku | P1 |
| T19 | **Workflow de orquestación** | `.github/workflows/extra-estilo-llm.yml` (copia también en la carpeta del extra): jobs preparar → datos → {zero-shot, LoRA, línea base+Reinhard} → comparar → resumen; papermill o nbconvert; artefactos (notebooks ejecutados, parejas, adaptador, mlflow.db, tabla, panel); caché de pip y de `HF_HOME`; `push` a `lab/**` y `workflow_dispatch` con entradas (N_EJEMPLOS, EPOCAS); permisos `contents: read`; `timeout-minutes` por job | YAML válido; prueba estática (ruta `.github/workflows/`, disparadores, `needs:` y nombres de artefactos coherentes entre subida y bajada) | T06–T10 [PICO] | Sonnet | P1 |
| T20 | **Run real y ensayo en fork limpio** | Run en verde en una rama `lab/` del repo del profesor (enlace, tiempos por job, artefactos); después, el mismo recorrido en un fork de otra cuenta (activar Actions, rama, run) con capturas | Los dos runs en verde con enlace; tiempos y límites del runner anotados; capturas revisadas | T19 | Sonnet + instructor | P1 |
| T21 | **Guía del pipeline en clase** | `guia-pipeline.md` con el formato de `guia-pipeline-e2e.md` de S3: guion del profesor por minutos, pasos del alumno (web y terminal), «qué debes ver» con los tiempos de T20, la tabla de comprobaciones del §11 | Cada cifra de T20; cada trampa del §11 con su respuesta | T20 | Sonnet | P1 |
| T22 | Checklist anti-fiasco | `checklist-actions.md` (1 página): ruta exacta del archivo, nombre de rama, Actions activado, run de prueba la víspera, enlace a un run verde de respaldo | Revisado contra el §11 | T20 | Haiku | P1 |
| T17 | Diapositiva-resumen | 1–3 diapositivas con el marco de los laboratorios de S3 (panel, tabla, mensaje) | Sin recursos externos; revisada en navegador | T10 | Sonnet | P2 |
| T18 | Revisión final y subida | Todas las pruebas en verde; `develop` solo, con orden expresa del instructor | Informe de lo comprobado | todo | Sonnet (Opus si se pide) | P1 |

## Orden y paralelismo
1. **Ahora:** T00 (pico, en curso).
2. **Tras el veredicto:** T01 (instructor) → T02, T03 (Haiku, en paralelo) → T04 (Sonnet) → T05 (Haiku).
3. **Notebooks:** T06 → T07 → (T08 y T09 en paralelo, dos agentes Sonnet) → T10.
4. **Orquestación:** T16 (Haiku) y T19 (Sonnet) → T20 (run real + ensayo en fork limpio, con el instructor) → T21 (Sonnet) y T22 (Haiku), en paralelo.
5. **Cierre:** T11 y T17 (Sonnet, en paralelo) → T12 (Sonnet) → T13 y T14 (Haiku, en paralelo) → T18.
6. **Opcional:** T15 cuando haya hueco.

## Brief común para los agentes (copiar al lanzar cada tarea)
- Repo `C:\bk\HC-Cursos\curso-ml-ia-desarrollo-produccion`, rama `develop`; **sin commit ni push** (lo hace el instructor o la tarea T18 con su orden).
- Crear/editar solo con Write/Edit/NotebookEdit; datos y modelos fuera del repo (`C:\bk\lab-estilo\`).
- Entorno: el venv del pico (ver `INFORME.md`), CPU, proxy corporativo.
- No inventar cifras: cada número sale de una celda ejecutada o del `INFORME.md` del pico; lo demás, «sin verificar».
- Sin rutas personales, correos ni credenciales, tampoco en las salidas de los notebooks.
- Tono: el de los laboratorios de S3 (frases cortas, «qué debes ver», «si falla»), para alumnos que no han visto LLM de visión.
