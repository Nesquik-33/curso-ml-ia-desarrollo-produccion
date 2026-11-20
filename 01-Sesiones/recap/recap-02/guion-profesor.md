# Guion del profesor · Recap 02 al empezar S3 (15 minutos)

Objetivo: que el grupo recuerde lo que S2 dejó construido (contrato, errores, imagen, contenedores, interfaz, workflow) **porque la demo de hoy parte de esa imagen**, y averiguar en el momento quién se queda sin proyecto de GCP, sin imagen o sin Docker, para no descubrirlo a la hora 2.
Reparto de la planificación de S3: 10 minutos de recap (diapositivas 1–13) y 5 de pregunta a mano alzada (diapositiva 14).

> **Preparado antes de S2 (15/11/2026).** S2 es el miércoles 18/11 y este guion está escrito sobre sus documentos, no sobre lo que ocurra. Se ajusta tras el miércoles (T19): tiempos reales, qué costó, quién tiene qué. Los apartados «Tras S2» de abajo dicen qué mirar.

## Antes de clase (5 minutos)

1. Abre `01-Sesiones/recap/recap-02/index.html` en el navegador y pulsa **F** (pantalla completa). **S** abre las notas del ponente; **O**, el índice.
2. Ten a mano una terminal en `04-Proyecto-Base` y, si quieres enseñar algo en directo, tu contenedor de S2 (`docker run --rm -p 8080:8080 retencion-api:local` y `curl http://127.0.0.1:8080/listo`). No es necesario: todo está en las diapositivas.
3. La lista de la diapositiva 14 es para contar, no para examinar: no pidas capturas, datos de tarjeta ni identificadores de proyecto en voz alta.

## En clase (15 minutos)

| Minuto | Diapositiva | Qué decir | Pregunta |
|---|---|---|---|
| 0:00 | 1 | S2 convirtió el modelo guardado en un servicio. Cinco piezas: modelo, API, imagen, contenedor, workflow | ¿Quién llegó a ver su contenedor responder en `/listo`? |
| 0:45 | 2 | Un archivo no es un servicio: falta contrato, validación, errores, registros, imagen y comprobación automática | Una frase: ¿qué le faltaba al modelo de S1? |
| 1:30 | 3 | El contrato no se escribe dos veces: viaja en la firma del modelo. Al arrancar se compara con `metadatos.json` y con el esquema `Cliente`; si no coincide, 503 con el motivo | ¿Qué respondió la API en la tarea al reentrenar con la variable nueva? |
| 2:30 | 4 | Pulsa los seis casos. Antes de abrir cada uno, pide el código. Idea que ordena todo: ¿quién se equivocó? 422 quien llama, 503 quien opera, 500 el desarrollador con el `id` | El ticket de 5 000 libras: ¿por qué no se rechaza? |
| 4:00 | 5 | Vivo no es listo: `/salud` decide si se reinicia; `/listo`, si se envía tráfico. Registro: una línea JSON con `id`, sin datos del cliente | ¿Por qué reiniciar un servicio sin modelo no lo arregla? |
| 5:00 | 6 | Pulsa las capas. Tres decisiones: dependencias antes del código (caché), usuario no root, `HEALTHCHECK` sobre `/salud`. Y lo que no entra, por `.dockerignore` | ¿Qué hay en el contexto que nunca debería estar? |
| 6:00 | 7 | Imagen = receta congelada; contenedor = imagen en ejecución. `-p` abre una puerta; `-v …:ro` monta datos fuera de la imagen | ¿Qué es `127.0.0.1` dentro de un contenedor? |
| 6:45 | 8 | Cuatro caminos y el contenedor dan la misma probabilidad (`0.8278889…`). La imagen pesa 826 MB; el usuario es 10001 | ¿Qué cambiaría si el orden de las columnas fuera otro? |
| 7:30 | 9 | La persona sabe el id; la API solo sabe de variables; la interfaz traduce. Dos imágenes (423 y 826 MB), red por nombre, API sin `-p`, datos en solo lectura | ¿Por qué la API no lleva `-p`? |
| 8:30 | 10 | El workflow repite todo en cada cambio y no publica nada (eso es S4). Los bloques del taller de S2, y el extra de punta a punta | ¿Quién llegó a ver el workflow en verde? |
| 9:15 | 11 | Autoevaluación: si hay prisa, una pregunta por mano alzada; si no, se salta | — |
| 10:00 | 12 y 13 | Puente: cada pieza local tiene su equivalente gestionado en GCP, y el código y la imagen no cambian; cambia dónde corre y lo que lo rodea. Sin cifras ni precios | ¿Qué creéis que cambia más: el código o la configuración? |
| 11:00 | 14 | **Diagnóstico a mano alzada**: cuenta y proyecto de GCP con facturación; imagen de S2 construida; Docker o Codespace. Cuenta con los botones **+** y **−** | Ver abajo |
| 15:00 | — | Cierra y pasa a la teoría de migración | — |

### La diapositiva 14, paso a paso (minutos 11–15)

1. Pregunta 1: «¿Quién tiene un proyecto de GCP con la facturación activada?». Cuenta y apunta el número.
2. Pregunta 2: «¿Quién tiene la imagen de S2 construida?» (en un Codespace, o al menos un workflow en verde). Cuenta y apunta.
3. Pregunta 3: «¿Quién puede ejecutar Docker, en su equipo o en un Codespace?». Cuenta y apunta.
4. Los que falten alguna de las tres siguen en modo **«solo mirar»** y usan el plan B de la planificación (D7): la sesión no se detiene. Anota nombres solo para ayudar después.
5. Anota los tres números en la planificación de S3; son la base de la decisión de T19.

## Si hay solo 5 minutos
Usa las diapositivas **1, 4, 8, 12 y 14** (una por minuto): el recorrido, los códigos de error, la prueba de que el contenedor da lo mismo que el código, el puente a GCP y el diagnóstico. El resto queda en el índice (**O**) por si alguien pregunta.

## Si algo sale mal

| Pasa | Haz |
|---|---|
| Alguien no recuerda qué es `/listo` | Diapositiva 5; en una frase: «¿puedes atender?». Vivo no es listo |
| Preguntan por qué hay dos imágenes | Diapositiva 9: la del modelo no debe llevar datos de clientes y cada pieza cambia por un motivo distinto |
| Preguntan si el recap menciona precios o regiones de GCP | No: sin cifras. Se verán, con su marca «sin verificar» si no se ejecutaron, en la teoría y las demos de S3 |
| Nadie tiene proyecto de GCP | Dilo así: la demo se sigue como recorrido y la tarea tiene su ruta sin nube. No se detiene la sesión |
| Las flechas no responden | Haz clic en la página una vez y repite; **Home** y **End** saltan al principio y al final |

## Tras S2 (T19, miércoles 18/11 por la tarde)

Marcar y completar con lo que de verdad pasó:

- [ ] Incidencias de S2 con Docker, el Codespace y el CI: ¿alguna diapositiva debe avisar de ellas (por ejemplo, la 7 o la 10)?
- [ ] Qué costó más: ¿se debe dar más peso a una diapositiva (contrato, códigos, capas, dos contenedores)?
- [ ] Cifras de la diapositiva 8 y 9: si en el Codespace del curso la imagen ocupa otra cifra, citar ambas con su origen.
- [ ] Quién tiene la imagen y Docker (anotar el número; la diapositiva 14 lo pregunta de nuevo el viernes).
- [ ] Decidir cuántos van al modo «solo mirar» y reflejarlo en la diapositiva 14.
- [ ] Reducir a 5 minutos si S2 se alargó y la teoría de S3 aprieta.
- [ ] Cambiar en `README.md` la nota «preparado antes de S2» por la fecha del ajuste.
