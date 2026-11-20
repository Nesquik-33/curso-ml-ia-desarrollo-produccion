# Rúbrica de la tarea S3 · avance 3 (100 puntos)

Es la rúbrica del avance 3 de tu caso: los mismos tres criterios y pesos que S1, S2 y [`rubrica-avance.md`](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md). Lo que se observa en cada criterio es nuevo (el avance 3 se concretó el 20/11/2026, al cambiar el plan de S3) y está marcado como **propuesta** hasta que el instructor lo confirme. La parte de GCP se evalúa igual con facturación que **sin facturación**: no tenerla no resta; fingir que se hizo algo, sí.

| Criterio | Peso | Qué se observa |
|---|---|---|
| **Reproducibilidad** | 20 | Otra persona clona tu rama `avance-3`, ejecuta tus pruebas con los comandos indicados y obtiene el mismo resultado que el runner. El workflow está en `.github/workflows/` y **se ejecutó de verdad**: hay enlaces a las ejecuciones en rojo y en verde y a sus commits, y la última de la rama está en verde. Versiones (Python y librerías) fijadas y cómo llegan los datos al runner, explicado. |
| **Técnica** | 40 | Workflow que se dispara en `push` a la rama y ejecuta todas tus pruebas; **al menos una prueba propia significativa que falla si se rompe la regla** y cuyo fallo provocó el rojo; permisos mínimos y ningún secreto; el arreglo que devuelve el verde es un cambio de código o de datos, no borrar ni saltar la prueba. GCP: cuenta de Google propia y Google Cloud activado (captura de la consola con el correo tapado); si el alta pidió facturación, presupuesto con alertas **antes de nada**; ningún recurso creado. |
| **Análisis y decisión** | 40 | Qué regla protege tu prueba y por qué importa en tu caso; qué pasó en el rojo (qué falló, cómo lo leíste en el registro) y qué cambió para el verde; diferencias entre tu Codespace y el runner, si las hubo; una decisión argumentada (por ejemplo, cómo llegan los datos al runner o qué pruebas corren en cada `push`); qué harás en S4 con el proyecto de GCP y qué riesgos de coste ves; **lo que no se hizo**, dicho con claridad y con el error exacto. |

## Qué se observa en cada parte (propuesta)

| | Lo mínimo para «Logrado» | Lo que lleva a «Sobresaliente» |
|---|---|---|
| Workflow | Se ejecuta en `push` a `avance-3`, instala dependencias y corre `pytest`; última ejecución en verde | Además: caché de dependencias, `timeout-minutes`, `concurrency` y un paso que solo se ejecuta si algo falla, cada uno con su porqué |
| Prueba propia | Una prueba que protege una regla del caso y falla si se rompe (comprobado) | Varias, cada una con la regla que protege, y la comprobación de que fallan descrita en la evidencia |
| Rojo → verde | Enlace a una ejecución en rojo por esa prueba y a la verde del arreglo | Además: el registro del rojo leído e interpretado (qué línea, qué valor) y el arreglo explicado |
| GCP | Cuenta de Google y Google Cloud activado, con la captura de la consola (correo tapado); si no se pudo, el motivo exacto | Además (opcional): proyecto desechable del curso, presupuesto con alertas y `gcloud` en el Codespace, listos para S4 |

## Niveles por criterio

| Nivel | Reproducibilidad (20) | Técnica (40) | Análisis (40) |
|---|---|---|---|
| Sobresaliente | 18–20 · un tercero reproduce sin ayuda y las ejecuciones enlazadas lo confirman | 36–40 · todo en verde, con pruebas propias que fallan si se rompe la regla y el rojo provocado por ellas | 36–40 · rojo y verde interpretados, decisión argumentada, riesgos y lo no hecho declarado |
| Logrado | 14–17 | 28–35 | 28–35 |
| En proceso | 8–13 · faltan pasos, versiones o algún enlace | 16–27 · el rojo no viene de una prueba, o la prueba propia no comprueba una regla | 16–27 · enlaces y salidas pegados sin interpretar |
| Insuficiente | 0–7 | 0–15 | 0–15 |

## Qué riesgos se esperan reconocidos
Elige los que correspondan a tu caso y explica qué harías:
- Una prueba que pasa en tu Codespace y falla en el runner (o al revés): datos que no están en el repositorio, versiones distintas, rutas absolutas.
- Una prueba que no puede fallar no protege nada: ¿cómo sabes que la tuya sí?
- «Arreglar» el rojo borrando, saltando o relajando la prueba.
- Un token o una clave en el repositorio o en el registro del workflow da acceso a quien lo lea.
- Un recurso de GCP olvidado sigue cobrando; una alerta de presupuesto avisa, pero no corta el gasto (compruébalo en la documentación vigente).
- Lo que **no** pudiste hacer y el error exacto.

## Descuentos y alertas
Topes **propuestos** para este avance, en línea con los de [`rubrica-avance.md`](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md):
- **Una credencial o un token en el repositorio** (también en el workflow, en su registro o en capturas): la técnica no supera 25.
- **Un workflow que nunca se ejecutó, o que solo se demuestra con capturas** sin enlace a las ejecuciones: la reproducibilidad no supera 8.
- **Presentar como hecho lo que no se hizo** (por ejemplo, un rojo que no existe, un presupuesto que no se creó o la ruta sin facturación presentada como si hubiera nube): el análisis no supera 20.
- **El verde se consiguió borrando, saltando o vaciando la prueba que daba rojo**, sin decirlo: la técnica no supera 25 (propuesta).
- **Recursos de GCP creados** antes de S4, o con facturación y **sin presupuesto previo**: el análisis no supera 25 (propuesta). No se aplica si no se creó nada.

## Lo que no se evalúa
- Que tengas facturación en GCP ni cuánto gastaste (no deberías gastar nada en este avance).
- La migración a GCP y el despliegue: pasan a S4.
- Cuántas pruebas tienes: cuenta que al menos una sea significativa y que el rojo → verde sea real.
