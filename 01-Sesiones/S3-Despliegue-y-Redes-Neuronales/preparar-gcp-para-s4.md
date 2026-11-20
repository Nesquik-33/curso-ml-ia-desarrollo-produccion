# Prepara tu GCP para S4 (sin crear nada todavía)

Hoja corta para el alumnado. En S4 (miércoles 25 de noviembre) llevamos tu caso a Google Cloud. Para no perder la sesión creando cuentas, llega con esto hecho.

> **Lo obligatorio para el [avance 3](tarea/README.md) es solo esto:** tener tu cuenta de Google y **activar Google Cloud** con ella (si el alta pide facturación, crea antes el presupuesto con alertas del paso correspondiente). El resto de la hoja (proyecto desechable, `gcloud` en el Codespace) es **recomendado** para llegar más rápido a S4, no obligatorio.

> **Qué no trae esta hoja, a propósito.** Ni precios, ni créditos o pruebas gratuitas, ni cuotas, ni los textos exactos de los botones de la consola: cambian y el curso no los ha comprobado. Todo eso está **sin verificar; consulta la página oficial** de Google Cloud en el momento de hacerlo y anota lo que veas tú.

## Reglas
- Una cuenta y un proyecto **tuyos**. Nunca la cuenta, el proyecto ni las credenciales de otra persona.
- Nunca pegues una clave, un token o un código de verificación en un chat, un correo, una incidencia ni un archivo del repositorio.
- El ID de tu proyecto, tu correo y el identificador de tu cuenta de facturación **no van al repositorio** ni a la evidencia (tápalos también en las capturas).
- **Sin facturación también vale.** Si no puedes o no quieres activarla, haz los pasos 1, 4 y 5 hasta donde se pueda y escribe en la evidencia qué no hiciste y por qué. No resta puntos.

## 1. Crea tu cuenta de Google Cloud
Entra en la consola oficial (`https://console.cloud.google.com/`) con una cuenta de Google personal o de estudiante. Si te ofrece una prueba gratuita o créditos, **lee sus condiciones en la página oficial antes de aceptar**: el curso no da cifras ni plazos (sin verificar).

## 2. Crea un proyecto nuevo y desechable
Un proyecto **solo para el curso**, que puedas borrar entero al terminar sin perder nada. Ponle un nombre genérico (por ejemplo, del estilo `curso-ml-ia-…`) que no lleve tu nombre ni tu correo. Anota su ID **fuera del repositorio**: lo necesitarás en S4.

## 3. Si activas la facturación: presupuesto con alertas ANTES de nada
- Vincula la facturación al proyecto **y, antes de cualquier otra cosa**, crea un **presupuesto** para ese proyecto con **alertas por umbrales** (por ejemplo, varios porcentajes del importe). El importe lo eliges tú: pequeño.
- **Una alerta avisa; no corta el gasto.** Así lo asume el curso: **compruébalo en la documentación vigente** de presupuestos de Cloud Billing y anota en la evidencia qué dice y dónde lo leíste.
- Comprueba a qué correo llegan los avisos.
- Dónde está cada opción en la consola: sin verificar en el curso; búscalo en la documentación oficial de Cloud Billing.

## 4. Qué NO crear todavía
Nada que pueda cobrar ni que haya que borrar después: **ni** buckets de Cloud Storage, **ni** datasets de BigQuery, **ni** repositorios de Artifact Registry ni imágenes, **ni** servicios de Cloud Run, **ni** secretos, **ni** cuentas de servicio o claves, **ni** máquinas virtuales, Cloud SQL o clústeres de GKE. **Tampoco** habilites APIs «por si acaso». Todo eso se hace en S4, juntos, con su limpieza el mismo día.

## 5. `gcloud` en tu Codespace (solo iniciar sesión y consultar)
Sigue [`sdk-google-cloud-vscode-y-codespaces.md`](../../03-Entorno/guias/sdk-google-cloud-vscode-y-codespaces.md) (borrador: sus órdenes están marcadas «sin verificar»; si algo falla, anota el mensaje exacto):
1. Instalar el SDK en el Codespace del curso (apartado A, opción 2): `bash 04-Proyecto-Base/deploy/gcp/instalar_sdk.sh --comprobar` y, si falta algo, sin `--comprobar`.
2. Iniciar sesión sin navegador propio (apartado B, paso 1): `gcloud auth login --no-launch-browser`.
3. Fijar **tu** proyecto por defecto: `gcloud config set project ID_DE_TU_PROYECTO`. **La región, todavía no:** se decide en S4.
4. Comprobar quién eres y la configuración: `gcloud auth list` y `gcloud config list`.
5. Comprobación de **solo lectura**: `gcloud projects describe ID_DE_TU_PROYECTO`. Si pide habilitar algo o activar la facturación, **no lo hagas por tu cuenta**: anótalo y lo vemos en S4.
6. Al terminar, para el Codespace. Si lo vas a borrar, cierra antes la sesión (`gcloud auth revoke`, apartado B, paso 5).

Sin facturación: los pasos 1, 2 y 4 deberían poder hacerse; lo que el 5 responda, anótalo tal cual.

## 6. Qué traer listo a S4
- [ ] Cuenta de Google Cloud y proyecto desechable creados (o, si no, el motivo escrito).
- [ ] Si hay facturación: presupuesto con alertas creado **antes** que cualquier otra cosa, y leído qué hace una alerta.
- [ ] Ningún recurso creado en el proyecto.
- [ ] Codespace del curso que arranca, con `instalar_sdk.sh --comprobar` sin nada que falte.
- [ ] `gcloud auth list` muestra tu cuenta activa y `gcloud config list` tu proyecto.
- [ ] El ID de tu proyecto a mano, **fuera** del repositorio.
- [ ] El avance 3 entregado, con su workflow en verde.
- [ ] La imagen de tu avance 2 se construye (en el Codespace o con tu workflow): la migración de S4 parte de tu servicio en local.
