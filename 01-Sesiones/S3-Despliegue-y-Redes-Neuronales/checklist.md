# Checklist S3

Plan de hoy (viernes 20 de noviembre, 10:00–14:00, hora de Perú): recap de S2 en laboratorio, laboratorio de GitHub Actions, GCP de palabra y tarea. **Hoy no se crea nada en GCP:** la migración pasa a S4.

## Antes de la sesión (docente)
- [ ] **Codespace propio listo** desde `develop`, ya arrancado (no crear uno nuevo en directo): en `04-Proyecto-Base`, `python -m ia_mlops.operacional` y `python -m ia_mlops.pipeline` **hechos**, con `data/processed/curso.db` y `models/modelo_mlflow/` presentes, y las pruebas rápidas en verde (`python -m pytest -q -m "not lento"`).
- [ ] La API y la interfaz de consulta arrancan en el Codespace y responden (es lo que usa el recap).
- [ ] **Fork propio** del repositorio del curso con Actions **activado** y la rama `lab/actions-s3` preparada según [`laboratorio-github-actions/guia.md`](laboratorio-github-actions/guia.md); al menos una ejecución en rojo y una en verde ya hechas, para enseñarlas si los runners van lentos.
- [ ] **Capturas de respaldo abiertas** en pestañas: las de los dos laboratorios y las ejecuciones roja y verde del *fork* del docente.
- [ ] Enlaces abiertos: [`laboratorio-recap-s2/index.html`](laboratorio-recap-s2/index.html), [`laboratorio-recap-s2/guia.md`](laboratorio-recap-s2/guia.md), [`laboratorio-github-actions/index.html`](laboratorio-github-actions/index.html), [`laboratorio-github-actions/guia.md`](laboratorio-github-actions/guia.md), [`preparar-gcp-para-s4.md`](preparar-gcp-para-s4.md), [`tarea/README.md`](tarea/README.md) y este [`guion.md`](guion.md).
- [ ] Repasar el bloque de GCP sin cifras: nada de precios, créditos ni cuotas; «sin verificar; consulta la página oficial».
- [ ] Tener a mano el enlace del formulario de Google del curso y el usuario de GitHub del instructor (para los repositorios privados).
- [ ] Parar el Codespace al terminar la sesión.

## Antes de la sesión (alumnado)
- [ ] Avance 2 entregado (vie 20, 10:00, hora de Perú) con el formulario de Google del curso.
- [ ] Codespace del curso que arranca, con `04-Proyecto-Base` y el entorno de S2 (si es nuevo: `python -m ia_mlops.operacional` y `python -m ia_mlops.pipeline`).
- [ ] Cuenta de GitHub con la sesión iniciada y un *fork* del repositorio del curso (si no lo tienes, lo creas en la pausa).
- [ ] El repositorio de tu caso propio en GitHub (el de los avances 1 y 2): lo necesitarás para la tarea.

## Durante la sesión (alumnado)
- [ ] Recap de S2: la interfaz llama a la API y la API responde; sabes qué variables de FS se calculan al vuelo y por qué con la misma lógica que al entrenar.
- [ ] Laboratorio de Actions: Actions activado en tu *fork*, la rama `lab/actions-s3` subida, **una ejecución en rojo provocada por una prueba** y **una en verde** tras el arreglo, con sus enlaces copiados.
- [ ] Sabes leer en el registro del workflow qué prueba falló y en qué línea.
- [ ] GCP: entiendes qué hay que traer listo a S4 y qué **no** se crea todavía.
- [ ] Tarea (avance 3) entendida y [`evidencias/plantilla-avance-3.md`](evidencias/plantilla-avance-3.md) descargada.

## Después de la sesión (alumnado, antes del miércoles 25 a las 10:00)
- [ ] Rama `avance-3` en el repositorio de tu caso, con el workflow que ejecuta tus pruebas.
- [ ] Al menos una prueba propia significativa que falla si se rompe la regla.
- [ ] Enlaces a la ejecución en rojo (por esa prueba) y a la verde del arreglo; la última ejecución de `avance-3`, en verde.
- [ ] Ninguna clave ni token en el repositorio ni en el registro del workflow.
- [ ] GCP preparado con [`preparar-gcp-para-s4.md`](preparar-gcp-para-s4.md): cuenta, proyecto desechable, presupuesto con alertas si hay facturación, **ningún recurso creado**, `gcloud` con sesión en el Codespace (o la ruta sin facturación, declarada).
- [ ] Evidencia y sección «Avance 3» de la plantilla del caso completadas; entrega con el formulario de Google del curso.
- [ ] Codespace parado al terminar.

## Registro de incidencias
Paso / esperado / obtenido / mensaje / acción. Sin credenciales ni identificadores. Prestar atención a lo que falle con **Actions en los *fork***, las ejecuciones en cola y el Codespace: es lo que más puede variar entre personas.
