# Pico S4 (extra): un LLM de visión que «lee» el estilo de color de una foto

Fecha: 20/11/2026. Portátil Windows 11 sin GPU (Intel Core Ultra 5 235U, 12 núcleos / 14 hilos lógicos, 31,4 GB de RAM). PyTorch con **12 hilos** (`ESTILO_HILOS=12`) en todas las medidas.

## Veredicto: **cambiar de enfoque** (y, si se mantiene el LLM, **llevarlo preentrenado**)

- **Técnicamente cabe en CPU**: el fine-tuning LoRA de SmolVLM-256M con 210 ejemplos y 3 épocas tarda **~19 min** (9 min de preparación + 10 min de entrenamiento) y el notebook 03 completo, **24 min**. Con 2,7 GB de memoria pico. En clase se podría lanzar en vivo con menos datos.
- **Pero el resultado no enseña lo que queremos enseñar**: B (LoRA) aprende el **formato** (100 % de JSON válidos) y **no la tarea**: escribe casi los mismos números para todas las fotos y su error (MAE normalizado 0,310) es **peor que contestar siempre la media** (0,259). A (zero-shot) es peor aún (0,433). La mejor versión con diferencia es una regresión sobre **27 estadísticas de color** (C_color, 0,151; ΔE con el objetivo 7,5 frente a 14,4 de no hacer nada), que entrena en segundos.
- Como **caso didáctico de producción** el resultado es muy bueno («mide una línea base barata antes de afinar un LLM»; «la pérdida baja y el formato es perfecto, pero el modelo no ha aprendido nada»), pero **no como demo de transferencia de estilo con un LLM**.
- Propuesta: mantener el extra con el **mensaje de las líneas base** (A/B/C/C_color/D). La segunda oportunidad del LLM (ronda 2, abajo) **no cambia el veredicto**.

## Ronda 2 (20/11/2026): segunda oportunidad para el LLM (tope de 1 h, de 22:11 a 22:52)

Mismo entorno (12 hilos), misma partición (210 train / 30 val / 60 test) y mismas métricas que la ronda 1. Todo con **sondas** fuera de los notebooks: `C:\bk\lab-estilo\scripts\ronda2.py` (resultados en `C:\bk\lab-estilo\ronda2\*.json`). Misma LoRA que B (r = 16 en q/k/v/o del modelo de lenguaje, tasa 5e-4, lote 4, codificador de imagen y conector congelados).

**Truco nuevo para que quepa en 1 h**: los rasgos de imagen de las 300 fotos se calcularon una vez (286 s, 120 reutilizados de la sonda B2) y se usan **también en la inferencia** (generación con `inputs_embeds`). Se comprobó con una foto que da el mismo texto que pasar la imagen («Dog running on grass.»). Por eso los s/foto de esta ronda (2,6–3,6 s) **no incluyen** el codificador de imagen (~2,2 s/foto) y no son comparables con los de la ronda 1.

| Versión (ronda 2) | Épocas | n test | MAE normalizado medio | Exactitud media (3 clases) | Formato correcto | Entrenamiento | Respuestas distintas |
|---|---|---|---|---|---|---|---|
| Referencias: «media» continua / «media» discretizada | – | 60 | 0,259 / 0,260 | – / 30 % | – | – | – |
| Referencias: C_color continua / C_color discretizada en las mismas 3 clases | – | 60 | 0,151 / 0,172 | – / 61 % | – | segundos | – |
| Ronda 1: B (imagen → JSON numérico) | 3 | 60 | 0,310 | – | 100 % | 1123 s | – |
| (1) VLM con LoRA, imagen → clases «bajo/normal/alto» | 2 | 60 | **0,257** (centro de cada clase) | **32 %** | 100 % | 460 s | 7 de 60 |
| (2a) Estadísticas en el prompt, solo texto, zero-shot (con arranque `{"exposicion":`) | 0 | 20 | 0,374 («media» en esas 20: 0,259) | – | 15 % | 0 | – |
| (2b) Estadísticas en el prompt + imagen, zero-shot (con arranque) | 0 | 20 | 0,279 («media»: 0,259) | – | 0 % | 0 | – |
| (2c) Estadísticas en el prompt, solo texto, LoRA → JSON numérico | 2 | 60 | **0,244** | – | 100 % | 494 s | 32 de 60 |
| (2d) Estadísticas en el prompt + imagen, LoRA → JSON numérico | **1** (por tiempo) | 60 | 0,262 | – | 100 % | 317 s | 13 de 60 |
| (3) SmolVLM-500M | – | – | no se probó (sin tiempo) | – | – | – | – |

Memoria pico del proceso: 3143 MB en 2c y 3673 MB en 2d.

Detalle:

- **(1) Clases.** Umbrales = terciles de train por ajuste; para el MAE, cada clase vale la media de train de esa clase. Exactitud por ajuste: exposición 37 %, temperatura 32 %, tinte 25 %, contraste 35 %, saturación 32 %, es decir, **al nivel del azar (33 %)**. Pérdida de validación 0,138 → 0,133. En las respuestas mostradas domina «normal». C_color discretizado igual acierta el 61 %, con un 72 % en exposición.
- **(2a/2b) Zero-shot con estadísticas.** El modelo sigue **copiando los rangos del prompt** («-1», «0.2 to 1.8») o copia las estadísticas («73», «42 8 8»). No sirve.
- **(2c) LoRA solo con texto.** Es la **única versión del LLM que mejora a «media»**, y por poco: 0,244 frente a 0,259. Mejora sobre todo en contraste (0,153 frente a 0,240 de «media»); temperatura 0,219, tinte 0,240, exposición 0,263 y saturación 0,345 (peor que «media»). Pérdida de validación 0,471 → 0,460. Inferencia 3,1 s/foto, sin imagen.
- **(2d) LoRA con imagen y estadísticas**, solo 1 época por el tope de tiempo: 0,262, al nivel de «media». Las respuestas mostradas son casi constantes. No es comparable del todo con 2c, que tuvo 2 épocas.

**Veredicto de la ronda 2: no.** Ninguna versión del LLM supera a «media» con claridad ni se acerca a C_color. La mejor (2c: estadísticas como texto, sin imagen, con LoRA) mejora a «media» en 0,015 de MAE normalizado, una diferencia pequeña para 60 fotos de test y una sola semilla. Queda a 0,09 de C_color, que hace lo mismo con una regresión lineal en segundos. Con un LLM de 135 M y 2 épocas, leer los números no supera a la regresión que recibe esos mismos números.

**Recomendación para los notebooks finales.** Mantener las versiones A, B (ronda 1), C, C_color y D. Añadir, si se quiere un último intento del LLM, la variante **2c (estadísticas en el prompt + LoRA)** como «¿y si le damos los números masticados?»: es barata (≈8 min de entrenamiento, sin codificador de imagen) y refuerza el mensaje. No recomiendo la versión con clases (1): no aprende y complica la explicación. Lo que no se probó (500M, más épocas, entrenar el conector) queda sin verificar.

## Ronda 3 (acto 3): el LLM explica el JSON en español (tope de 45 min, de 23:27 a 23:55)

**Tarea de lenguaje.** Dado el JSON de ajustes, escribir una explicación corta en español. Notebook nuevo `05_explicar_estilo.ipynb`, ejecutado con sus salidas y con la misma interfaz de CI: celda `parameters`; lee `parejas/parejas.jsonl` de la carpeta de trabajo; deja `resultados/metricas_explicacion.json`, `resultados/explicaciones.jsonl`, `adaptador_explicacion/` y los runs `A3_explicacion_one_shot` y `B3_explicacion_lora` en `mlflow.db`.

- **Modelo:** la parte de lenguaje de SmolVLM-256M-Instruct, sin imagen (licencia «apache-2.0»). Es el que ya estaba en caché, y así la comparación con las rondas anteriores es directa.
- **Frases objetivo fabricadas con reglas** (`comun_estilo.frase_objetivo`). La intensidad es |valor − neutro| / (media anchura del rango). Por debajo de 0,15 el ajuste se ignora; por debajo de 0,5 es «un poco»; si no, «bastante». El orden de los ajustes es fijo y hay 3 plantillas, elegidas por el hash del id de la foto.
- **Métricas automáticas** por expresiones regulares (`comun_estilo.evaluar_frase`):
  - % de ajustes relevantes mencionados en el sentido correcto;
  - % mencionados en sentido contrario;
  - % de frases que mencionan un ajuste no relevante (alucinación);
  - % de frases en español y con 20–300 caracteres;
  - % de frases perfectas.
  Las frases objetivo sacan el 100 % en todo (comprobado en `05`, celda 3).
- **Configuración:**
  - A3: one-shot, con un ejemplo de train en el prompt.
  - B3: la misma LoRA que 2c (r = 16 en q/k/v/o, tasa 5e-4, lote 4), 2 épocas, 210 frases de train; 134 tokens por ejemplo.
  - Ambas se evalúan en las 60 frases de test.

| Versión | Ajustes en el sentido correcto | En sentido contrario | Frases con alucinación | Español y longitud correctos | Frases perfectas | s/frase |
|---|---|---|---|---|---|---|
| Objetivo (reglas) | 100 % | 0 % | 0 % | 100 % | 100 % | – |
| A3 one-shot | 36,0 % | 43,5 % | 53,3 % | 100 % | 1,7 % | 6,86 |
| B3 LoRA (2 épocas) | 60,5 % | 38,7 % | 58,3 % | 100 % | 6,7 % | 3,71 |

Origen: `05`, celdas 4, 6 y 7.

- **Tiempos:** A3 tardó 412 s para 60 frases. El entrenamiento de B3 tardó 447 s; la pérdida de validación bajó de 0,279 a 0,186 entre la época 1 y la 2. El notebook completo tardó 1117 s, y la prueba tipo CI con papermill (N = 16, 1 época) 114 s, sin errores.
- **Adaptador:** 7,06 MB. **Memoria pico del proceso:** 3019 MB.
- **Ejemplos reales** (6, lado a lado, en `05`, celda 7):
  - A3 repite la frase de su ejemplo para cualquier JSON y luego sigue escribiendo el prompt («Ahora tú: Ajustes: …»); parte de sus alucinaciones vienen de ese eco.
  - B3 escribe frases impecables con la plantilla. En los 6 ejemplos nombra los cinco ajustes, con «un poco/bastante» y sentidos a menudo equivocados. Por ejemplo, con temperatura −0,08 escribe «se sube un poco la temperatura», y con saturación 1,73 escribe «se baja un poco la saturación».

**Veredicto: «el LoRA mejora claramente: no».** B3 mejora a A3 en sentido correcto (60,5 % frente a 36,0 %) y en frases perfectas (6,7 % frente a 1,7 %), y la forma es perfecta. Pero invierte el 38,7 % de los ajustes, alucina en más de la mitad de las frases y solo acierta del todo en 4 de 60. Con dos sentidos posibles, acertar el 60 % está poco por encima del azar. Como lección didáctica es valiosa: el texto suena bien y es falso, y solo lo detecta una métrica automática contra la verdad. Para explicar un JSON, las reglas (100 %) bastan. Sin verificar: más épocas o más datos, que la pérdida de validación todavía bajaba.

**Recomendación:** incluir el 05 como «acto 3» solo si se presenta así («fluido no es correcto»). En el extra, la explicación para el usuario debería salir de `frase_objetivo` aplicada al JSON de C_color.

**Corrección (20/11/2026):** C_color usa **27** estadísticas de color, no 33: en Lab, media, desviación y percentiles 5/50/95 (15 números); en RGB, media, desviación y percentiles 1/99 (12). Lo comprobó otro agente ejecutando el código y las cifras no cambian. Corregido en este informe, en `comun_estilo.py` y en el notebook 04, que se volvió a ejecutar.

## Ronda 4 (acto 3): muchos JSON fabricados (tope de 75 min, de 23:55 a 01:12)

**Criterio fijado antes de medir:** en las mismas 60 frases de test de la ronda 3, al menos un 90 % de ajustes en el sentido correcto **y** como mucho un 10 % de frases con alucinación.

- **Datos:** los JSON de train se fabrican con `muestrear_ajustes` (semilla 4, sin fotos) y sus frases con `frase_objetivo`. Val y test son los de las parejas.
- **Modelo:** la misma LoRA que en la ronda 3 (r = 16 en q/k/v/o, tasa 5e-4, lote 4).
- **Sondas:** `C:\bk\lab-estilo\scripts\ronda4.py`, con resultados en `C:\bk\lab-estilo\ronda4\`.
- **CPU compartida en (a) y (b):** por el tope de tiempo las lancé en paralelo, (a) con 12 hilos y (b) con 6. Las muestras de CPU del sistema durante el entrenamiento de (b) alternan entre un 86 % y un 5–6 %. Antes de empezar la carga era del 34 %. Sus tiempos están inflados.

| Variante | Entrada | N train | Épocas | Pérdida de val. por época | Sentido correcto | Sentido contrario | Frases con alucinación | Español y longitud | Frases perfectas | Entrenamiento | s/frase | Memoria pico |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ronda 3, B3 (referencia) | JSON | 210 (de las parejas) | 2 | 0,279 / 0,186 | 60,5 % | 38,7 % | 58,3 % | 100 % | 6,7 % | 447 s | 3,71 | 3019 MB |
| (a) | JSON | 1000 fabricados | 2 previstas; **cortada tras la 1.ª** | 0,102 / – | sin medir | sin medir | sin medir | sin medir | sin medir | 1899 s la 1.ª época (CPU compartida) | – | – |
| (b) sonda | «fácil»: sentido e intensidad precalculados | 500 fabricados | 2 | 0,061 / 0,027 | **100 %** | 0 % | **10,0 %** | 100 % | 90,0 % | 1968 s (6 hilos, CPU compartida) | 10,3 (compartida) | 2853 MB |
| (b) en el notebook 05 final | «fácil» | 500 fabricados | 2 | 0,061 / 0,032 | **100 %** | 0 % | **18,3 %** | 100 % | 81,7 % | 906 s (12 hilos, solo) | 4,11 | 2887 MB |
| A3 one-shot en el notebook 05 final | «fácil» | – | – | – | 40,7 % | 39,5 % | 58,3 % | 0 % | 0 % | 0 | 4,51 | – |

- **(a):** la corté a las 00:40 para que cupieran la variante (b) y la ejecución del notebook. Solo midió la pérdida de validación de la época 1: 0,102, frente a 0,279 de la ronda 3 en la época 1. Con 1000 ejemplos aprende más, pero **no hay medida en test**.
- **(b):** cumple el criterio en la sonda, justo en el límite (10,0 % de alucinación). Al **repetir la misma configuración** en el notebook (12 hilos, sin competencia), el sentido sigue al 100 % pero la alucinación sube al 18,3 %. Los dos runs no son idénticos: cambian el número de hilos y el orden de las operaciones, y quizá el redondeo.
- **De qué son las alucinaciones** en el notebook (11 frases, script `ver_alucinaciones.py`): todas mencionan un ajuste casi nulo, con intensidad entre −0,12 y 0,13, por debajo del umbral de 0,15. Casi siempre es un adjetivo de más en la primera mitad de la frase, sobre todo «más oscura»; la lista de acciones suele estar bien.
- **A3 one-shot** con la entrada fácil sigue sin servir: mezcla el ejemplo y sigue escribiendo el prompt.

**Veredicto contra el criterio: se cumple en la sonda (100 % / 10,0 %), pero no de forma reproducible (100 % / 18,3 % en la ejecución del notebook).** El sentido correcto (≥ 90 %) se cumple con holgura en las dos. La alucinación (≤ 10 %) queda en el límite en una y por encima en la otra. Lo honesto es decir que **el LoRA ya redacta bien y acierta siempre el sentido, pero aún se inventa algún adjetivo**. El formato JSON (a) no se pudo evaluar.

**Configuración recomendada para el 05 final** (ya actualizada y ejecutada; tarda 1454 s en este portátil):
- **Clase:** `N_FRASES = 500`, `EPOCAS = 2`, `FORMATO = "facil"`. Es el valor por defecto.
- **CI:** `-p N_FRASES 100 -p EPOCAS 1`. Sin verificar.
- **Lo siguiente que probaría** para bajar la alucinación por debajo del 10 % (sin verificar): más JSON (1000–2000) con el formato fácil, o una plantilla sin la lista de adjetivos.

El notebook 05 tiene dos parámetros nuevos, `N_FRASES` y `FORMATO`, y la función nueva `comun_estilo.entrada_explicacion`. MLflow tiene los runs A3 y B3 nuevos; los de la ronda 3 están marcados como borrados.

## Cifras medidas (ejecución de referencia: 300 fotos, 210 train / 30 val / 60 test, 224 px, 3 épocas)

Todas salen de las salidas de los notebooks ejecutados (orden de ejecución: 00 → 01 → 03 → 02 → 04; el 03 se ejecutó antes que la versión final del 02, y son independientes). «Celda» = número de celda de código en orden, empezando en 1.

### Lectura de los ajustes y transferencia (tabla de `04`, celda 5; `resultados/tabla_comparativa.csv`)

| Versión | MAE normalizado medio (0 = perfecto) | Formato correcto | ΔE2000 medio con el objetivo | Distancia de histogramas con la referencia | SSIM con el contenido | s/foto (inferencia) | s entrenamiento | MB modelo |
|---|---|---|---|---|---|---|---|---|
| sin cambio | – | – | 14,41 | 0,534 | 1,000 | – | – | – |
| objetivo (ideal) | – | – | 0,00 | 0,391 | 0,820 | – | – | – |
| media de train | 0,259 | – | 14,72 | 0,535 | 0,988 | – | – | – |
| A zero-shot (con arranque `{"exposicion":`) | 0,433 | 55 % | 22,21 | 0,594 | 0,815 | 5,05 | 0 | 493,9 |
| B LoRA | 0,310 | 100 % | 15,99 | 0,552 | 0,937 | 4,91 | 1123 (530 prep. + 593 entr.) | 493,9 + adaptador 7,06 |
| C MobileNetV3-small + Ridge | 0,229 | – | 13,21 | 0,508 | 0,948 | 0,011 (0,005 en la última ejecución) | 2,2 (1,1) | 9,71 |
| C_color (27 estadísticas + Ridge) | 0,151 | – | 7,50 | 0,414 | 0,860 | sin medir aparte | 4,5 (2,6), incluye inferencia de test | 0,001 |
| D Reinhard (Lab) | – | – | 14,37 | 0,241 | 0,779 | 0,039 (0,015) | 0 | 0 |

Los tiempos entre paréntesis son de la última ejecución del 04, tras la corrección de «27». Las métricas no cambian; los tiempos de C, C_color y D varían de una ejecución a otra.

«neutro» (contestar «no se tocó nada») da MAE normalizado 0,259, igual que «media» (tabla de `04`, celda 5). Tiempos de C: `04`, celda 3. MAE normalizado por ajuste en el mismo sitio; p. ej. B: exposición 0,299, temperatura 0,342, tinte 0,285, contraste 0,317, saturación 0,308 (`03`, celda 5).

### Tiempos, tamaños y memoria

| Medida | Valor | Origen |
|---|---|---|
| Instalación de transformers, peft, accelerate, scikit-image, nbconvert, ipykernel, psutil sobre el venv con torch | 102 s | comando pip (fuera de los notebooks) |
| Primera descarga + carga de SmolVLM-256M-Instruct (494 MB) | 51,7 s | script de sonda (fuera de los notebooks) |
| Descarga con el modelo ya en caché | 0,1 s | `00`, celda 3 |
| Descarga de MobileNetV3-small (9,8 MB) | 1,3 s | `00`, celda 3 |
| Notebook 01: extraer 300 fotos del images.tar.gz local (792 MB) a 224 px + fabricar parejas | 12–15 s el notebook completo | tiempo de nbconvert |
| Notebook 02 completo (60 fotos) | 320 s | tiempo de nbconvert |
| A: inferencia | 5,05 s/foto (mín. 2,67, máx. 8,39) | `02`, celda 4 |
| B: preparar 240 ejemplos (codificador de imagen una vez por foto) | 530 s (≈2,2 s/foto) | `03`, celda 3 |
| B: entrenamiento LoRA, 3 épocas, lote 4 | 593 s, 159 pasos, 3,73 s/paso | `03`, celda 4 |
| B: inferencia | 4,91 s/foto | `03`, celda 5 |
| Notebook 03 completo | 1456 s (24 min) | tiempo de nbconvert |
| Notebook 04 completo | ≈40 s | tiempo de nbconvert |
| Parámetros entrenables LoRA (r = 16, q/k/v/o del modelo de lenguaje) | 1 843 200 de 258 328 128 (0,71 %) | `03`, celda 2 |
| Tamaño del adaptador (`adapter_model.safetensors`) | 7,06 MB | `03`, celda 5 |
| Pesos del modelo base (safetensors) | 493,9 MB | `03`, celda 5 |
| Memoria pico del proceso (A, inferencia) | 1541 MB | `02`, celda 5 (psutil, peak working set) |
| Memoria pico del proceso (B, entrenamiento + inferencia) | 2747 MB | `03`, celda 5 |
| Pérdida de validación por época (0 → 3) | 2,758 → 0,479 → 0,476 → 0,475 | `03`, celda 4 |
| Sonda previa: paso de 4 ejemplos con prompt largo (265 tokens) sin caché de imagen / con caché | 20–21 s / 8,5–9,2 s (8 hilos) | script de sonda |

### Lo que se ve en las respuestas reales

- A sin arranque: describe la foto («The image shows a dog running on a grassy field…») y no escribe JSON (`02`, celda 4).
- A con arranque `{"exposicion":`: escribe un JSON, pero **copia los extremos de los rangos del prompt** («0.7», «-1», «0.2», a veces «-1 green to 1 magenta») e inventa claves (`02`, celda 6).
- B: JSON perfecto y casi constante: `{"exposicion": 0.22, "temperatura": 0.62, "tinte": 0.62, "contraste": 0.82, "saturacion": 0.68}` para fotos muy distintas (`03`, celda 5).

## Decisiones técnicas (y por qué)

- **SmolVLM-256M-Instruct**: el VLM más pequeño con soporte directo en transformers (Idefics3: SigLIP 86 M + conector 7 M + SmolLM2 135 M). Cabe en CPU y entrena con LoRA en minutos. No se probaron la versión de 500 M ni Moondream (sin tiempo; sin verificar). La imagen entra **sin trocear** (`do_image_splitting=False`): 64 «palabras de imagen» en lugar de 1088; con troceo la sonda tardó 35,9 s en generar frente a 5,2 s.
- **Codificador de imagen y conector congelados; LoRA solo en q/k/v/o del modelo de lenguaje** (como pedía el encargo). Truco de CPU: como el codificador está congelado, sus salidas se calculan una vez por foto y se reutilizan en todas las épocas (`comun_estilo.preparar_ejemplo`).
- **Prompt corto** para B (`"Color edits as JSON."`): 135 tokens por ejemplo en vez de 265.
- **Cinco ajustes** con fórmula exacta en `comun_estilo.aplicar_ajustes` (exposición, temperatura, tinte, contraste, saturación, en ese orden y recorte final). Valores uniformes en su rango, 2 decimales.
- **Métricas**: MAE por ajuste y normalizado por el rango; ΔE CIEDE2000 con el **objetivo** (el contenido con los ajustes reales de la referencia, que conocemos porque los datos son fabricados); distancia de Bhattacharyya de histogramas L, a, b con la referencia; SSIM en grises con el contenido.
- **C_color** se añadió tras ver que C (MobileNet) apenas mejora a «media»: una sonda con estadísticas de color dio 0,151 y se incorporó al notebook 04.

## Para GitHub Actions (requisitos del profesor y del borrador `extra-estilo-llm.yml`)

- Notebooks: `00_preparar_entorno`, `01_datos_fabricados`, `02_zero_shot`, `03_fine_tuning_lora`, `04_comparar_y_transferir` (.ipynb), cada uno con celda `parameters` (N_EJEMPLOS, EPOCAS, RESOLUCION, MODELO, CARPETA_TRABAJO; el 04 además ETAPA `c_d`/`completo`). Por defecto leen variables de entorno `ESTILO_*` y, si no, valores pequeños (N_EJEMPLOS = 60, EPOCAS = 2).
- Carpeta de trabajo: `ESTILO_TRABAJO` (por defecto `_trabajo/` junto a los notebooks, en `.gitignore`); caché: `HF_HOME` (por defecto `<trabajo>/hf`); pesos de torchvision en `$HF_HOME/torch`. Sin rutas de Windows.
- Entradas y salidas: 01 → `parejas/` (+ `fotos_<res>/`); 02 → `resultados/pred_A.jsonl`, `metricas_A.json`; 03 → `adaptador/`, `resultados/pred_B.jsonl`, `metricas_B.json`, `mlflow.db` + `mlartifacts/`; 04 `c_d` → `resultados/pred_C.jsonl`, `metricas_C.json`, `metricas_D.json`; 04 `completo` → `resultados/tabla_comparativa.csv` y `.json`, `resultados/panel_transferencia.png` y runs A, C, C_color, D y comparativa en el mismo `mlflow.db`.
- **Cosas a corregir o tener en cuenta en el workflow**:
  1. **MLflow**: para que no se pisen bases al juntar artefactos, solo escriben en `mlflow.db` el 03 (run B con el adaptador) y el 04 `completo` (A, C, C_color, D, comparativa). 02 y 04 `c_d` solo dejan JSON. Ojo: el orden de `download-artifact` en el job «comparar» importa si dos artefactos traen el mismo archivo; con este reparto solo `adaptador-lora` trae `mlflow.db`.
  2. **Fotos**: el 01 descarga Oxford-IIIT Pet (~800 MB) de la web oficial si no hay `ESTILO_TAR`; la guarda en el directorio temporal del sistema (no en la carpeta de trabajo, para que no viaje en los artefactos). En CI esa descarga no se ha probado (sin verificar); conviene cachearla con `actions/cache` o preparar las fotos en el 00.
  3. Los artefactos «metricas-a», «adaptador-lora» y «metricas-c-d» excluyen `parejas/**` pero incluyen `fotos_<res>/` (unos MB con N pequeño).
  4. El workflow asume `requisitos-extra-estilo.txt` y una carpeta `pruebas/` junto a los notebooks: dejo `requisitos-extra-estilo.txt` en esta carpeta (versiones medidas; el índice de PyTorch CPU para Linux está **sin verificar**); `pruebas/` no existe aquí. También hay que copiar `comun_estilo.py` junto a los notebooks.
  5. Los notebooks guardan figuras en `figuras/` relativa al directorio de ejecución (con papermill, el de `--cwd`, o el del notebook).
- **Tamaño mínimo para CI**: ver sección siguiente.

## Ejecución pequeña tipo CI (papermill, N_EJEMPLOS = 16, EPOCAS = 1)

Se ejecutó la cadena completa como la haría el workflow: papermill con `-p N_EJEMPLOS 16 -p EPOCAS 1`, `--cwd` distinto de la carpeta de los notebooks y `PYTHONPATH` apuntando a `comun_estilo.py`; el 04 dos veces (`-p ETAPA c_d` y luego `-p ETAPA completo`). Todo terminó **sin errores** (salidas en `C:\bk\lab-estilo\ci_nb\`, datos en `C:\bk\lab-estilo\trabajo_ci\`). Ojo: se ejecutó a la vez que la sonda B2, así que los tiempos están inflados por la competencia por la CPU.

| Notebook | Tiempo (Windows, 12 hilos, con CPU compartida) |
|---|---|
| 00 | 13 s |
| 01 (11 train / 1 val / 4 test) | 13 s |
| 02 | 104 s (A: 15,1 s/foto por la competencia) |
| 03 | 120 s (entrenamiento 52 s incluida la preparación) |
| 04 `c_d` | 24 s |
| 04 `completo` | 19 s |

Resultado con N = 16 y 1 época: **B no llega ni a aprender el formato** (formato correcto 0 %; sus métricas son las de «sin cambio») y con 4 fotos de test las cifras no significan nada (p. ej. C_color 0,209 frente a «media» 0,279). Sirve para **probar el pipeline**, no para enseñar resultados.

**Tamaño mínimo didáctico (estimación, sin verificar)**: en la ejecución grande B ya escribe JSON válidos tras la primera época (53 pasos; pérdida de validación 0,479). Para CI propongo **N_EJEMPLOS = 60, EPOCAS = 2** (42 train, ≈22 pasos): estimo ≈5 min para el 03 y ≈1 min para el 02 en este portátil, a partir de 2,2 s/foto de preparación, 3,7 s/paso y 5 s/foto de inferencia medidos; en un runner de GitHub (4 vCPU) sin verificar. Si se quiere solo comprobar que todo corre, N = 16 y 1 época (medido arriba).

## Versiones de librerías (`00`, celda 2)

Python 3.11.18; torch 2.15.0+cpu; torchvision 0.29.2+cpu; transformers 5.23.0; peft 0.22.0; accelerate 1.16.0; huggingface_hub 2.4.0; mlflow 3.18.0; scikit-learn 1.9.1; scikit-image 0.26.0; numpy 2.4.6; pillow 13.0.0; matplotlib 3.11.2; nbconvert 7.17.2; ipykernel 7.4.0; papermill 2.7.0 (solo para la prueba tipo CI).

## Licencias

- **SmolVLM-256M-Instruct**: «apache-2.0», leída de la ficha de Hugging Face (metadatos, comprobado con `model_info` en `00`, celda 3, y en la web de la ficha).
- **MobileNetV3-small** (pesos ImageNet de torchvision): el código de torchvision es BSD-3-Clause; la licencia de los **pesos**: no se pudo comprobar (la ficha de Hugging Face de `google/mobilenet_v3_small_100_224` dio 401 y los pesos usados son los de torchvision, no esos).
- **Oxford-IIIT Pet**: CC BY-SA 4.0. Cita: O. M. Parkhi, A. Vedaldi, A. Zisserman, C. V. Jawahar, «Cats and Dogs», CVPR 2012. Las imágenes derivadas (paneles) heredan CC BY-SA 4.0.
- Reinhard et al., «Color Transfer between Images», IEEE CG&A 2001 (método, sin licencia de software).

## Riesgos

- **El mensaje de la demo**: si se presenta como «el LLM aprende a copiar estilos», los números lo desmienten. Hay que presentarlo como caso de evaluación honesta.
- **Tiempo en CPU**: 24 min el 03 con 300 fotos; en portátiles de alumnos (sin verificar) puede ser más. En vivo, solo con N pequeño.
- **Variabilidad**: una sola semilla y un solo reparto; con 60 fotos de test las diferencias pequeñas (p. ej. C frente a «media») pueden no ser significativas. Sin verificar con otras semillas.
- **CI**: descarga de 800 MB de fotos y ~500 MB de modelo por run; el job 03 es el más lento. Linux, índice de PyTorch CPU y descarga de fotos sin probar.
- Avisos de Hugging Face «unauthenticated requests» en las salidas (sin token; inocuo).

## Qué no se pudo medir

- SmolVLM-500M, Moondream u otros VLM (sin tiempo).
- Variantes de B que quizá aprendan la tarea: más épocas, más datos, LoRA en las MLP, entrenar el conector, otra tasa de aprendizaje, predecir valores discretizados. Ver la sonda B2 abajo.
- Repetición con otras semillas; ejecución real en GitHub Actions; memoria en Linux.
- Tiempo de inferencia de C_color por foto por separado (se midió junto con su entrenamiento).

## Sonda B2 (fuera de los notebooks)

Para descartar que el fallo de B fuera solo de configuración se probó una variante (script `C:\bk\lab-estilo\scripts\sonda_b2.py`): LoRA r = 16 en **todas** las lineales del modelo de lenguaje (q/k/v/o + gate/up/down), tasa 1e-3, 120 fotos de train, 4 épocas (120 pasos), evaluada en 20 fotos de val.

- Preparación 141 s; entrenamiento 659 s (con la CPU compartida con la ejecución tipo CI).
- Pérdida media por época: 0,694 → 0,479 → 0,474 → 0,470 (se estanca igual).
- MAE normalizado en val: **0,303**, frente a 0,285 de «media» en esas 20 fotos: **tampoco aprende**. Las respuestas alternan entre 3–4 JSON casi fijos (p. ej. `{"exposicion": 0.18, "temperatura": -0.08, "tinte": -0.09, "contraste": 0.92, "saturacion": 0.89}`).

Conclusión de la sonda: con este tamaño de datos y de entrenamiento, el problema no parece la configuración de LoRA. Hipótesis (sin verificar): las 64 «palabras de imagen» de SigLIP tras el conector conservan poca información fina de color, o hacen falta muchos más pasos. Siguientes pruebas posibles (sin verificar): entrenar también el conector, cuantizar los valores en pocas clases («cálida/neutra/fría»), dar al modelo las estadísticas de color como texto en el prompt, o más datos y épocas con GPU.

## Propuesta para el extra (duración y qué se hace en vivo)

- **Duración: 45–60 min**.
- 5 min: idea (fabricar datos con etiqueta exacta) con `figuras/01_cada_ajuste.png` y `01_antes_despues.png`; ejecutar el 01 en vivo (15 s).
- 10 min: el 02 en vivo con 3–5 fotos (5 s por foto): ver al modelo describir la foto y copiar los rangos.
- 10 min: el 03 **preentrenado** (llevar el adaptador y el notebook ejecutado); en vivo, como mucho una época con N pequeño para ver bajar la pérdida.
- 10 min: el 04 en vivo (≈40 s): tabla y panel; discusión «¿quién gana y por qué?».
- 10–15 min: conexión con la S4 (MLflow con los runs y el adaptador; el workflow de Actions con un job por notebook).

## Archivos

- Notebooks ejecutados: `00_preparar_entorno.ipynb`, `01_datos_fabricados.ipynb`, `02_zero_shot.ipynb`, `03_fine_tuning_lora.ipynb`, `04_comparar_y_transferir.ipynb`; módulo común `comun_estilo.py`; `requisitos-extra-estilo.txt`; `.gitignore`.
- Figuras (PNG con paleta de 256 colores): `figuras/01_cada_ajuste.png`, `figuras/01_antes_despues.png`, `figuras/03_curva_perdida.png`, `figuras/04_panel_transferencia.png`.
- Fuera del repo (`C:\bk\lab-estilo\`): `trabajo\` (fotos, parejas, resultados, adaptador, `mlflow.db`, `mlartifacts\`), `hf\` (caché de modelos), `scripts\` (sondas), `trabajo_ci\` y `ci_nb\` (ejecución pequeña tipo CI).
