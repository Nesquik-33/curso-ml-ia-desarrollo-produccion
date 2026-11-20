# Guion del docente · S3 (240 min)

Viernes 20 de noviembre, de 10:00 a 14:00 (hora de Perú). **Plan del día cambiado:** la S3 deja de ser «migración a GCP en vivo». Hoy se repasa S2 con un laboratorio, se hacen los laboratorios de MLflow y de GitHub Actions, se enseña una red neuronal como extra y GCP se explica de palabra para que el grupo llegue a S4 con la cuenta preparada. La migración a GCP pasa a **S4** (miércoles 25). La planificación de [`00-Planificacion/s3/`](../../00-Planificacion/s3/PLANIFICACION-S3.md) era el plan previo: sirve de referencia para S4, no para hoy.

Lo que se dice en el aula separa lo **comprobado** de lo **sin verificar** (en particular, todo lo de GCP: hoy no se ejecuta nada en la nube).

## Bloques

| Hora (Perú) | Min | Qué se hace | Material | En vivo / capturas |
|---|---|---|---|---|
| 10:00–10:10 | 10 | **Bienvenida y plan del día.** Contar el cambio de plan en un minuto: hoy repaso de S2 y GitHub Actions; GCP de palabra; la migración, en S4. Recordar que el avance 2 se entregó hoy a las 10:00. | Este guion · [`README.md`](README.md) | En vivo |
| 10:10–11:20 | 70 | **1 · Laboratorio-recap de S2: el servicio.** La interfaz de consulta, la inferencia con la API y el cálculo al vuelo de las variables de FS. Cada persona en su Codespace; el docente proyecta. La presentación está pensada para 90 min: para caber en 70, la diapositiva 19 (dos contenedores, opcional) queda como lectura y la 10 (422) y la 13 se cuentan rápido. | [`laboratorio-recap-s2/index.html`](laboratorio-recap-s2/index.html) · [`laboratorio-recap-s2/guia.md`](laboratorio-recap-s2/guia.md) | En vivo en el Codespace del docente; capturas de respaldo |
| 11:20–11:55 | 35 | **2 · Laboratorio de MLflow: de dónde sale el modelo.** La base del proyecto, la interfaz en el puerto 5000, los runs y sus métricas, comparar modelos (el `train_auc` de 1,000 del boosting), la firma, las versiones del registro, reentrenar → versión 2 y cargarlo desde Python (0,828, lo mismo que la API). De 45 a 35 min: la parte A (qué es) en 3 min, porque ya se vio en S1. | [`laboratorio-mlflow/index.html`](laboratorio-mlflow/index.html) · [`laboratorio-mlflow/guia.md`](laboratorio-mlflow/guia.md) | En vivo; capturas de respaldo |
| 11:55–12:10 | 15 | **Pausa.** Pedir que, durante la pausa, quien no tenga *fork* del repositorio del curso lo cree (hace falta en el siguiente bloque). | — | — |
| 12:10–13:20 | 70 | **3 · Laboratorio de GitHub Actions: cada cambio se comprueba solo.** Romper y arreglar un workflow de pruebas en la rama `lab/actions-s3` del *fork* de cada alumno. Que cada persona vea su propio rojo y su propio verde, con enlace. De 90 a 70 min: el run tarda ~1 min (medido), así que hay margen; «Si algo falla» (diapositiva 19) queda como lectura. | [`laboratorio-github-actions/index.html`](laboratorio-github-actions/index.html) · [`laboratorio-github-actions/guia.md`](laboratorio-github-actions/guia.md) · [`laboratorio-github-actions/pruebas-proyecto.yml`](laboratorio-github-actions/pruebas-proyecto.yml) | En vivo en el *fork* del docente; capturas de respaldo |
| 13:20–13:40 | 20 | **4 · Extra: red neuronal, ¿perro o gato?** Transferencia (MobileNetV3-small congelada + regresión logística), entrenar en segundos, registrarla en MLflow como un modelo más y predecir una foto; qué significa 93 % (6 fallos de 90). En clase se enseña con las capturas; replicarlo es autoestudio (la instalación de PyTorch tarda ~1,5 min). | [`laboratorio-red-neuronal/index.html`](laboratorio-red-neuronal/index.html) · [`laboratorio-red-neuronal/guia.md`](laboratorio-red-neuronal/guia.md) | Con capturas (entrenar en vivo solo si el Codespace del docente responde) |
| 13:40–14:00 | 20 | **GCP de palabra (5 min) · tarea (avance 3) y cierre (15 min).** GCP: para S4 hace falta la cuenta de Google con Google Cloud activado; presupuesto con alertas antes de nada si piden facturación (una alerta avisa, no corta el gasto: que lo comprueben); no crear nada todavía. Sin precios ni cuotas: «sin verificar; consulta la página oficial». Tarea: workflow de pruebas en el repositorio del caso propio con una prueba propia significativa, rojo → verde con enlaces y verde al entregar, más Google Cloud activado. Entrega: miércoles 25 a las 10:00 (hora de Perú), formulario de Google del curso. Preguntas. | [`preparar-gcp-para-s4.md`](preparar-gcp-para-s4.md) · [`tarea/README.md`](tarea/README.md) · [`tarea/rubrica.md`](tarea/rubrica.md) · [`evidencias/plantilla-avance-3.md`](evidencias/plantilla-avance-3.md) | En vivo; GCP solo explicado, **no se crea nada** |

Total: 10 + 70 + 35 + 15 + 70 + 20 + 20 = **240 min**.

**Por qué este orden:** primero el servicio (recap de S2), luego de dónde sale el modelo que sirve (MLflow), luego cómo se comprueba cada cambio (Actions, la base de la tarea) y al final el extra, que reutiliza MLflow con otro tipo de modelo.

## Mensajes que no deben perderse
- **Recap de S2:** la interfaz no tiene el modelo; llama a la API. Las variables de FS que el cliente no trae se calculan al vuelo con la misma lógica que al entrenar (si no, el modelo recibe otra cosa).
- **MLflow:** cada entrenamiento queda anotado (parámetros, métricas, huella de datos) y el modelo que se sirve es una **versión concreta** del registro, con su firma; por eso cargarlo da lo mismo que la API.
- **Red neuronal:** es un modelo más: se registra, se versiona y se sirve igual; lo nuevo es la entrada (una imagen) y la transferencia (la red ya sabía de perros y gatos por ImageNet).
- **GitHub Actions:** un workflow que no puede ponerse rojo no protege nada. El rojo tiene que venir de una prueba, y el verde de un arreglo, no de borrar la prueba.
- **GCP:** hoy no se crea nada. Presupuesto antes que cualquier recurso. Nadie está obligado a pagar: la ruta sin facturación vale.
- **Avance 3:** se entrega con enlaces a las ejecuciones; una captura sola no lo demuestra.

## Si el tiempo se descontrola
- Orden de recorte: 1.º el extra de red neuronal (pasa a autoestudio con su guía); 2.º el final del recap (que quede como lectura); 3.º en MLflow, el paso 11 (cargar desde Python). **No se recorta** el laboratorio de Actions (es la base de la tarea) ni la tarea y el cierre.
- GCP puede quedarse en 2 min con la hoja [`preparar-gcp-para-s4.md`](preparar-gcp-para-s4.md) como lectura obligatoria.
- Si el Codespace del docente no responde (hoy se detuvo dos veces al entrenar la red neuronal), todo el material lleva capturas y salidas reales: se sigue con ellas.

## Si algo falla en directo

| Síntoma | Respuesta |
|---|---|
| El Codespace no arranca o se queda en modo recuperación | Esa persona sigue con un compañero (pantalla compartida) y anota el mensaje exacto; el docente sigue con el suyo. Si es el del docente, pasar a las capturas del laboratorio. No se detiene la sesión. Plan B para el laboratorio de Actions: no necesita Codespace, se puede editar el workflow desde la web de GitHub. |
| Falta `curso.db` (la API o la interfaz no encuentran datos) | En `04-Proyecto-Base`: `python -m ia_mlops.operacional` y después `python -m ia_mlops.pipeline` (es lo que hace falta en un Codespace nuevo, como en S2). |
| Puerto ocupado | Cerrar la otra API, interfaz o contenedor que lo usa, o arrancar en otro puerto (por ejemplo `--port 8081`) y usar ese en las llamadas. |
| Actions desactivado en el *fork* (la pestaña Actions no muestra ejecuciones) | En los *fork*, GitHub suele traer los workflows desactivados: entrar en la pestaña **Actions** del *fork* y activarlos con la opción que ofrece GitHub allí; después, un `push` nuevo a `lab/actions-s3`. Comprobar también que el disparador del workflow incluye esa rama. |
| Una ejecución se queda en cola | Esperar unos minutos: los runners compartidos pueden tardar. Mientras, comprobar que el disparador y la rama son los correctos. Si no arranca, enseñar la ejecución del *fork* del docente (o sus capturas) y que la persona lo compruebe más tarde: el rojo → verde de la tarea lo hace en su casa. |
| El workflow falla por el YAML, no por una prueba | Leer el mensaje de GitHub (suele señalar la línea); es el error más frecuente con la sangría. Aprovecharlo: «esto también es un rojo, pero no es el que pide la tarea». |
| Alguien pregunta por precios, créditos o cuotas de GCP | «Sin verificar en el curso; consulta la página oficial y anota lo que veas». No dar cifras. |
