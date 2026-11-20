# Tarea S3 · Tus pruebas en GitHub Actions y Google Cloud activado para S4

**Esta tarea es el avance 3 de tu caso propio (Bank Marketing).** No hay un ejercicio aparte sobre Online Retail II.

**Entrega:** a las 10:00 (hora de Perú) del **miércoles 25 de noviembre**, antes de que empiece S4 · repositorio personal de tu caso con la rama `avance-3` (o carpeta comprimida si no hay repositorio, aunque entonces la parte (a) no se puede demostrar: ver «Honestidad»). Se entrega con el **formulario de Google del curso** (el instructor da el enlace en clase): tu nombre, el número de avance (3), el enlace a tu rama o carpeta y «qué no pude ejecutar». Si tu repositorio es privado, añade al instructor como colaborador (su usuario lo indica en clase) para que pueda ver el código y las ejecuciones. Para ramas: [`git-y-ramas.md`](../../../07-Recursos/guias/git-y-ramas.md).

> **Cambio de plan, dicho claro.** La versión anterior de esta tarea era «migrar tu caso a GCP y desplegar el servicio». **Ya no vale:** la migración a GCP pasa a **S4**. En S3 se repasó S2 (interfaz, API y variables de FS calculadas al vuelo) y se hizo el laboratorio de GitHub Actions; GCP solo se explicó de palabra para que llegues a S4 con la cuenta preparada.

## Qué se pide
Dos partes. Las dos cuentan; la (a) es la que más pesa.

**(a) Un workflow de GitHub Actions que ejecuta las pruebas de tu caso**, en el repositorio de tu caso propio:
1. El workflow vive en `.github/workflows/` de **tu** repositorio y ejecuta tus pruebas (`python -m pytest`, o lo que uses) en cada `push` a la rama `avance-3` (y, si quieres, en `pull_request` y a mano con `workflow_dispatch`).
2. **Al menos una prueba propia significativa**: una que proteja una regla de tu caso y que **falle si se rompe la regla** (por ejemplo, que `duration` no entra en el modelo, que `raw = master + descartes`, o que tu API rechaza con 422 un valor imposible). Una prueba que solo comprueba que «algo existe» no cuenta como significativa.
3. **El historial rojo → verde demostrado**: una ejecución en **rojo** provocada por esa prueba (rompes la regla a propósito, o aprovechas un fallo real) y la ejecución en **verde** del commit que lo arregla. Entregas los **enlaces a las dos ejecuciones** y los dos commits. El rojo tiene que venir de **una prueba que falla**, no de un error de sintaxis del YAML ni de una dependencia que no se instala (esos también se anotan, pero no sustituyen al rojo de la prueba).
4. **El workflow en verde al entregar**: la última ejecución de la rama `avance-3` es verde.
5. **Sin secretos**: el workflow no necesita ninguno. Permisos mínimos (`permissions: contents: read`). Ni claves, ni tokens, ni `.env` en el repositorio.

**(b) Tu cuenta de Google y Google Cloud (GCP) activado.** Es lo único que se pide de GCP en este avance:
1. Tener una **cuenta de Google** propia.
2. **Activar Google Cloud** con esa cuenta: entrar en la consola de Google Cloud y completar el alta. Si el alta te pide activar la facturación o una prueba, sigue [`preparar-gcp-para-s4.md`](../preparar-gcp-para-s4.md) y crea antes un **presupuesto con alertas** (una alerta avisa, pero no corta el gasto: compruébalo en la documentación vigente).
3. **No crees nada más** (ni proyectos de trabajo, ni buckets, ni servicios): todo eso es S4.
4. Si no puedes activarlo, dilo con el motivo exacto: no resta puntos; fingirlo, sí. Nunca uses la cuenta de otra persona.

Recomendado, no obligatorio, para llegar más rápido a S4: crear el proyecto desechable del curso e instalar `gcloud` en el Codespace ([`preparar-gcp-para-s4.md`](../preparar-gcp-para-s4.md)).

## Dónde se hace
- La parte (a), en el repositorio de **tu caso** (el de los avances 1 y 2), con la misma mecánica que el [laboratorio de GitHub Actions](../laboratorio-github-actions/guia.md) de hoy. Puedes partir del workflow del laboratorio ([`pruebas-proyecto.yml`](../laboratorio-github-actions/pruebas-proyecto.yml)) o del de S2 ([`ci.yml`](../../../04-Proyecto-Base/deploy/github-actions/ci.yml)) y adaptarlo a tu caso: carpeta del proyecto, versión de Python, cómo se instalan tus dependencias y qué orden ejecuta tus pruebas. Lo que copies y lo que cambies, anótalo.
- Si tus pruebas necesitan datos (el CSV de Bank Marketing o tu SQLite), **decide cómo llegan al runner** y explícalo en la decisión de la evidencia: subir el CSV al repositorio (con la cita de la fuente que exige su licencia), generar los datos en el propio workflow o usar una muestra pequeña de prueba. Ninguna es la «correcta»; lo que se evalúa es que funcione y que lo justifiques.
- La parte (b), en la consola de Google Cloud desde el navegador. (Opcional para S4: `gcloud` en el Codespace con [`sdk-google-cloud-vscode-y-codespaces.md`](../../../03-Entorno/guias/sdk-google-cloud-vscode-y-codespaces.md), borrador «sin verificar».)

## Pasos
1. Crea la rama `avance-3` desde tu rama del avance 2 (o desde la que tengas al día) y súbela.
2. Añade el workflow y haz `push`. Mira la pestaña **Actions** de tu repositorio. Si no aparece ninguna ejecución, comprueba que Actions está activado en tu repositorio (en un *fork* suele venir desactivado) y que el disparador incluye tu rama.
3. Deja las pruebas en verde en el runner. Si fallan allí y no en tu Codespace, la diferencia es información: anota cuál era (datos que no estaban, una versión distinta, una ruta absoluta…).
4. Escribe (o elige) tu prueba propia significativa y comprueba en local que **falla si rompes la regla**.
5. **Rojo:** sube un commit que rompa la regla. Copia el enlace de la ejecución en rojo y el nombre de la prueba que falló.
6. **Verde:** sube el commit que lo arregla. Copia el enlace de la ejecución en verde.
7. Activa Google Cloud con tu cuenta de Google (presupuesto con alertas antes, si el alta pide facturación). **Nada más.**
8. Completa [`evidencias/plantilla-avance-3.md`](../evidencias/plantilla-avance-3.md) (cópiala a tu repositorio) y la sección «Avance 3» de [`plantilla-avance.md`](../../../02-Proyecto-Transversal/alumno/plantilla-avance.md).
9. Comprueba que la última ejecución de `avance-3` está en verde y entrega con el formulario.

## Evidencia mínima
- El archivo del workflow en tu rama `avance-3`.
- **Enlace a la ejecución en rojo** (y su commit), con el nombre de la prueba que falló y la línea del error.
- **Enlace a la ejecución en verde** del commit que lo arregla, y enlace (o captura acompañada del enlace) de la **última ejecución en verde** al entregar.
- Salida de `python -m pytest -q` en tu Codespace.
- Qué comprueba tu prueba propia, qué regla protege y cómo comprobaste que falla si se rompe.
- GCP: una frase que confirme que tienes cuenta de Google y Google Cloud activado, y una captura de la página de inicio de la consola **con tu correo tapado**. Si activaste facturación, si creaste el presupuesto (sin importes ni identificadores). Si no pudiste, el motivo.
- `evidencias/plantilla-avance-3.md` y la sección del avance 3 de `plantilla-avance.md` completadas.

## Rúbrica
Ver [`rubrica.md`](rubrica.md): 20 % reproducibilidad, 40 % técnica, 40 % análisis y decisión.

## Honestidad
No se evalúa solo por capturas: una captura de una ejecución verde **sin enlace** a la ejecución no la demuestra. Si algo no lo pudiste hacer (Actions desactivado, sin repositorio en GitHub, sin facturación, `gcloud` que no inicia sesión), escríbelo con el **error exacto**: declararlo es parte de lo que se evalúa. No pegues en el repositorio ni en la evidencia claves, tokens, códigos de verificación, el ID de tu proyecto, tu correo ni el identificador de tu cuenta de facturación (tapa también las capturas). Cita la ayuda que recibiste (personas, documentación y herramientas, incluidas las de IA) y para qué.
