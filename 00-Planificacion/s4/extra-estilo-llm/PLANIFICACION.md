# Planificación · Extra de S4: un LLM de visión que copia el estilo de color de una foto

Estado: **borrador del 20/11/2026**, preparado mientras corre el estudio técnico (`00-Planificacion/s4/_pico_llm_estilo/`). Todo lo que dependa de sus mediciones va marcado **[PICO]** y se rellena con su `INFORME.md`; no se escribe ninguna cifra antes.
Tareas: [`TAREAS.md`](TAREAS.md).

Reglas del curso que aplican (las mismas de S1–S3): solo `develop`; no inventar cifras (lo no medido, «sin verificar»); sin rutas personales, correos ni credenciales en nada publicable; licencias comprobadas y citadas; material didáctico, sobrio, con salidas reales.

---

## 1. Qué es y para quién

**El ejercicio.** El alumno da una **foto de referencia** (el estilo: p. ej. un atardecer cálido) y una **foto de contenido**. Un **LLM de visión pequeño**, ajustado con **LoRA**, «lee» el estilo de la referencia como un JSON de ajustes de color (temperatura, saturación, contraste…), y esos ajustes se aplican a la foto de contenido. Se compara con tres alternativas para decidir con datos qué hace falta de verdad.

**Encaje en el curso.** Extra de **S4** (no obligatorio, no entra en la tarea ni en la rúbrica), en **`01-Sesiones/S4-Orquestacion-y-CI-CD/extra-estilo-llm/`** (decidido el 20/11/2026). Reutiliza lo ya visto: transferencia y modelo congelado (laboratorio de red neuronal de S3), MLflow (laboratorio de S3), comparar modelos con métricas (S1). **Con S4 (CI/CD) se conecta de lleno (decidido el 20/11/2026): los mismos notebooks se orquestan como un pipeline en GitHub Actions** (§11), un job por etapa, como el pipeline de datos e2e de S3.

**Lo que el alumno entiende al terminar:**
1. Qué es un **LLM de visión** (imagen + texto → texto) y qué es **LoRA** (entrenar unos pocos millones de parámetros encima de un modelo congelado).
2. Que a veces los **datos de entrenamiento se fabrican**: si controlamos el proceso (aplicamos ajustes conocidos), la respuesta correcta es gratis.
3. Que un modelo se juzga **contra una línea base**: zero-shot frente a ajustado; LLM frente a una red pequeña; y frente a un método clásico sin aprendizaje.
4. Que lo que se despliega es un **adaptador versionado** en MLflow (unos MB), no una copia entera del modelo.
5. Cuándo **no** hace falta un LLM (si la red pequeña o el método clásico empatan).

## 2. Formato: notebooks

Cuatro notebooks cortos, **ejecutados con sus salidas** (el alumno ve el resultado aunque no los ejecute), cada uno con explicación en texto, poco código y una imagen por idea.

| # | Notebook | Qué hace | Dura (clase) |
|---|---|---|---|
| 0 | `00_preparar_entorno.ipynb` | Comprueba versiones, descarga el modelo y las fotos, comprueba memoria e hilos | [PICO] |
| 1 | `01_datos_fabricados.ipynb` | Define los ajustes, aplica ajustes aleatorios conocidos, enseña antes/después, reparte train/val/test | [PICO] |
| 2 | `02_zero_shot.ipynb` | Versión A: prompt al VLM, parsear el JSON, medir el error; respuestas reales buenas y malas | [PICO] |
| 3 | `03_fine_tuning_lora.ipynb` | Versión B: LoRA, curva de pérdida, error en test, tamaño del adaptador, registro en MLflow | [PICO] |
| 4 | `04_comparar_y_transferir.ipynb` | Versiones C y D, tabla comparativa, panel de transferencia de estilo, conclusiones | [PICO] |

Opcional: `05_prueba_tu_foto.ipynb` (subir dos fotos propias y ver el resultado) y una diapositiva-resumen de 1 página para proyectar.

**Qué se hace en vivo y qué se lleva hecho:** lo decide el veredicto del pico (**[PICO]**: «entrenable en clase» / «llevar preentrenado» / «cambiar de enfoque»). Por defecto, sin datos: 01, 02 y 04 en vivo; 03 ejecutado antes y en clase solo se recorre.

## 3. Requisitos

### 3.1 Hardware
- **Mínimo previsto:** CPU, sin GPU (portátil del alumno o Codespace de 2 núcleos y 8 GB). Si no cabe en 8 GB, se dice y se ofrece la ruta «solo leer los notebooks ejecutados». Memoria máxima medida: **[PICO]**.
- **Aviso Codespaces:** el 20/11/2026 el Codespace del profesor se detuvo dos veces al entrenar (sospecha de cuota). El extra debe poder seguirse **sin ejecutar** (notebooks con salidas) y en local.

### 3.2 Software (versiones exactas: [PICO])
| Paquete | Para qué |
|---|---|
| Python 3.11 (el del curso) | — |
| `torch` y `torchvision` (CPU) | redes; la misma instalación que el laboratorio de red neuronal |
| `transformers`, `peft`, `accelerate` | el VLM y LoRA |
| `pillow`, `numpy`, `scikit-image` | ajustes de color, espacio Lab, SSIM |
| `mlflow` (3.18, el del curso) | registrar runs y el adaptador |
| `jupyter` / `ipykernel` | notebooks |
| `matplotlib` | paneles |

Fichero `requisitos-extra-estilo.txt` con versiones fijadas (tarea T03). **No** se añade nada a `requirements-*.txt` del proyecto base (el extra va aparte para no engordar la imagen de la API).

## 4. Qué hay que descargar

| Qué | Origen | Licencia | Tamaño | Estado |
|---|---|---|---|---|
| VLM alumno (candidato SmolVLM-256M-Instruct; alternativa 500M u otro) | Hugging Face | **[PICO]** (comprobar en la ficha) | **[PICO]** | por medir |
| MobileNetV3-small preentrenada (línea base C) | torchvision | pesos: licencia **sin verificar** (ya anotado en el pico de red neuronal) | 10,3 MB (medido el 15/11) | ya probado |
| Oxford-IIIT Pet `images.tar.gz` | VGG, Universidad de Oxford | CC BY-SA 4.0 (verificada el 15/11) | 791,9 MB (medido) | ya probado |
| (Opcional) fotos propias del profesor para los ejemplos de clase | el profesor | del profesor | — | pendiente de decidir |

Descarga y caché fuera del repositorio. En el repositorio solo van los notebooks, las imágenes de los paneles (pequeñas) y, si se decide, un subconjunto pequeño de fotos con su atribución.

## 5. Datasets que hay que construir

| Conjunto | Cómo se hace | Para qué |
|---|---|---|
| **Fotos base** | Subconjunto de Oxford-IIIT Pet (resolución y número: [PICO]), recorte centrado, misma función de preparación en todos los notebooks | materia prima |
| **Parejas fabricadas** (train/val/test) | A cada foto base se le aplican ajustes aleatorios **conocidos** (4–6 parámetros, rangos fijados, semilla fija) → (foto editada, JSON de ajustes) | entrenar y medir A, B, C |
| **Parejas de transferencia** | 3–4 parejas (referencia con estilo marcado, contenido distinto) elegidas a mano y fijadas por nombre de archivo | el panel visual final |
| **(Opcional) Fotos del alumno** | dos fotos suyas | `05_prueba_tu_foto.ipynb` |

Definición de cada ajuste (fórmula exacta, rango y unidad): **[PICO]**, y se copia tal cual a los notebooks y a una tabla del README del extra. Una prueba comprobará que aplicar el JSON a la foto original reproduce la foto editada (si no, las etiquetas fabricadas no valen).

## 6. Métricas (definidas igual en todos los notebooks)

| Métrica | Qué mide | Versiones |
|---|---|---|
| Error medio absoluto por parámetro | cuánto se aleja el JSON predicho del real | A, B, C |
| JSON válido (%) | cuántas respuestas del LLM se pueden leer | A, B |
| Parecido de color con la referencia | distancia entre histogramas o ΔE medio en Lab | A, B, C, D |
| Conservación del contenido | SSIM con la foto de contenido | A, B, C, D |
| Tiempo (entrenar, por foto) y tamaño (base y adaptador) | coste | A, B, C, D |

## 7. Estructura de carpetas propuesta

```
01-Sesiones/S4-Orquestacion-y-CI-CD/extra-estilo-llm/
  README.md                     qué es, requisitos, cómo seguirlo (con y sin ejecutar), licencias
  requisitos-extra-estilo.txt
  00_preparar_entorno.ipynb … 04_comparar_y_transferir.ipynb  (+ 05 opcional)
  estilo/                        módulo pequeño compartido: ajustes de color, métricas, carga del VLM (para no repetir código)
  img/                           paneles y ejemplos (pequeños)
  pruebas/test_extra.py          pruebas rápidas sin modelo (ver §8)
```
Ubicación por confirmar con el instructor («módulo 4» = S4; alternativa `06-Modulo-LLMs/`).

## 8. Calidad y pruebas

- **Pruebas sin descargar modelos** (`pytest`): los ajustes son reproducibles (aplicar el JSON a la original da la editada); las métricas devuelven valores conocidos en casos triviales (misma imagen → SSIM 1); Reinhard no cambia una imagen consigo misma; los notebooks tienen salidas guardadas, no tienen rutas personales y sus celdas de texto existen; las imágenes citadas existen.
- **Revisión didáctica** (tarea aparte): cada notebook se entiende leyendo solo el texto; ningún término sin explicar; cada cifra sale de una celda.
- **Revisión visual** de los paneles (mirar cada imagen).
- Índice de S4 (`contenido_indices.py`) con el extra enlazado.

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| LoRA del VLM demasiado lento en CPU | lo mide el pico; plan B preentrenado; plan C: LLM de texto que recibe estadísticos de color en vez de la imagen |
| El VLM no devuelve JSON válido | medir el % válido; prompt con ejemplo; el fine-tuning debería arreglarlo (se mide) |
| La red pequeña (C) empata o gana al LLM (B) | es un resultado válido y didáctico: se discute «¿hacía falta un LLM?» |
| Licencia del VLM no compatible con uso docente | elegir otro candidato; se anota |
| Descargas bloqueadas por el proxy o lentas | medido en el pico; caché preparada; notebooks ejecutados como respaldo |
| Codespace sin cuota | el extra se sigue leyendo los notebooks ejecutados o en local |

## 10. Decisiones del instructor
1. ~~Ubicación~~ **Decidido (20/11/2026):** `01-Sesiones/S4-Orquestacion-y-CI-CD/extra-estilo-llm/`.
2. ~~Fotos de los ejemplos de clase~~ **Decidido (20/11/2026):** Oxford-IIIT Pet (CC BY-SA 4.0).
3. Duración en clase y qué parte en vivo — tras el veredicto del pico. *Pendiente.*
4. ~~CI opcional~~ **Decidido (20/11/2026):** la orquestación en GitHub Actions es parte central del extra (§11).

## 11. Orquestación en GitHub Actions (parte central)

**Idea.** Los mismos notebooks, sin copiarlos a scripts, se ejecutan como pipeline: cada notebook es un **job**, los jobs se encadenan con `needs:` y se pasan su salida como **artefacto** (igual que el pipeline de datos e2e de S3, que funcionó el 20/11/2026 en 6 min 49 s). El alumno ve en la pestaña Actions el grafo del experimento y descarga el adaptador, la tabla y el panel como artefactos.

**Grafo propuesto** (`.github/workflows/extra-estilo-llm.yml`):
```
preparar (00) ─► datos (01) ─┬─► zero-shot (02, versión A) ─────────┐
                             ├─► fine-tuning LoRA (03, versión B) ──┼─► comparar (04: tabla + panel) ─► resumen
                             └─► línea base (C) y Reinhard (D) ─────┘
```
- **Ejecutar notebooks:** con `papermill` (parámetros por job) o `jupyter nbconvert --execute`; cada notebook ejecutado se sube como artefacto, para que se vea con sus salidas. Elección: [PICO]/T19.
- **Parámetros pequeños en CI** (N_EJEMPLOS, EPOCAS, RESOLUCION) — los fija el pico; `workflow_dispatch` con entradas para cambiarlos a mano.
- **Caché** de pip y de la descarga del modelo (`actions/cache` sobre `HF_HOME`), para no descargarlo en cada job.
- **Resumen** en `$GITHUB_STEP_SUMMARY`: la tabla A/B/C/D y enlaces a los artefactos.
- **MLflow:** base SQLite dentro del artefacto del job de fine-tuning (como en el pipeline e2e); no se usa servidor.
- **Límites a comprobar** (sin verificar hoy): memoria y núcleos del runner estándar de GitHub, tiempo máximo por job, tamaño de artefactos y caché. Se miden en T20 con un run real.

**Lecciones del 20/11/2026 (Actions «fue un fiasco» en clase) que se convierten en comprobaciones:**
| Lo que pasó | Comprobación antes de clase |
|---|---|
| El archivo del workflow quedó en la raíz (`workflow-ac`) y no aparecía en Actions | La guía dice el nombre exacto `.github/workflows/extra-estilo-llm.yml`; captura de dónde se crea; prueba que comprueba la ruta |
| La rama no coincidía con el disparador (`actions-clase` frente a `lab/**`) | Disparador documentado en la primera diapositiva; `workflow_dispatch` además del `push`; la guía dice qué nombre de rama usar |
| En un fork, Actions puede venir desactivado | Ensayo real con un fork de otra cuenta (T20) y captura del aviso |
| Codespace detenido (cuota) | Todo se puede hacer desde la web de GitHub; el pipeline corre en los runners de GitHub, no en el Codespace |
| Copiar YAML tecleando rompe la sangría | Ofrecer el archivo listo para copiar (botón «Raw») y validar el YAML en una prueba |
