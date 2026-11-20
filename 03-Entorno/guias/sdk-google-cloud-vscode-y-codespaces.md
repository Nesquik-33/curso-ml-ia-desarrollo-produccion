# SDK de Google Cloud en VS Code (Windows) y en el Codespace

Guía del alumnado de «ML e IA: de desarrollo a producción», sesión S3. Cómo instalar `gcloud` y conectarte a Google Cloud desde el terminal de VS Code, sin pegar nunca una clave.

> **Estado.** Nada de esto se ha ejecutado todavía en un Codespace real ni en Windows: la prueba única es la tarea T36. Cada orden sale de la documentación de Google Cloud (leída el 15/11/2026) y lleva la marca **sin verificar** hasta que se pruebe. Si algo falla, anota el mensaje exacto y envíaselo al instructor.

## Reglas que valen para toda la guía

- **Nunca** pegues una clave JSON, un token o el código de verificación en un chat, un correo, una incidencia ni un archivo del repositorio. Ni siquiera «para que me ayuden».
- Esta guía solo **inicia sesión y consulta**: no crea nada. Los comandos que crean recursos (y pueden costar dinero) están en la guía de migración y los ejecutas tú con el instructor.
- Los costes dependen de lo que crees, no de instalar el SDK. Mira los precios en la consola de Google Cloud; aquí no hay cifras. Al terminar el curso se borra todo lo creado (la guía de migración lleva la limpieza).
- Si no tienes una cuenta de facturación (o no quieres activarla): sigue el recorrido sin nube de la guía de migración; esta guía te sirve solo hasta el paso 4. No actives pruebas gratuitas por tu cuenta sin leer sus condiciones.

# A · Instalar el SDK

## Opción 1: Windows, para el terminal de VS Code de escritorio (sin verificar)

1. Descarga el instalador oficial: `https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe` (página de Google: `https://docs.cloud.google.com/sdk/docs/install`).
2. Ejecútalo y sigue el asistente. Deja marcada la opción de Python incluido, salvo que sepas lo que haces. Desmarca «iniciar el shell de Google Cloud CLI» (configuraremos todo a mano).
3. **Cierra VS Code por completo y ábrelo de nuevo** (si no, el terminal no ve el PATH nuevo). Abre un terminal (`Ctrl+ñ`) y escribe:

```
gcloud version
```

**Qué debes ver:** una lista con «Google Cloud SDK» y un número de versión.
**Si falla** («no se reconoce como nombre de un cmdlet»): reinicia el equipo y repite; si sigue, abre el terminal de VS Code en CMD en lugar de PowerShell. Si el asistente se queda al descomprimir, ejecútalo como administrador. Si lo habías desinstalado antes, reinicia antes de reinstalar (indicaciones de Google).

## Opción 2: el Codespace del curso (sin verificar)

El Codespace por defecto **no trae** el SDK, para que quien solo hace S2 no pague tiempo de arranque. Elige una de las dos formas:

**a) Instalarlo bajo demanda** (la que usaremos en la demo). En el terminal del Codespace:

```
bash 04-Proyecto-Base/deploy/gcp/instalar_sdk.sh --comprobar
bash 04-Proyecto-Base/deploy/gcp/instalar_sdk.sh
```

La primera orden no instala nada: dice qué falta. La segunda instala lo que falte (puede tardar unos minutos), no repite lo ya instalado y termina con las versiones de `gcloud`, `bq`, `gcloud storage`, `kubectl` y `gke-gcloud-auth-plugin`.

**Qué debes ver:** cinco líneas `[OK   ]` y al final `SDK LISTO`.
**Si falla:** si ves `[FALTA]`, vuelve a ejecutar el script (es repetible); si el error es de red al descargar, espera un minuto y repite. Si persiste, copia el mensaje y avísanos. Plan B: Cloud Shell (terminal de Google Cloud en el navegador), que ya trae `gcloud`, pero no trae `env-ia-mlops` y hay que traer el repositorio.

**b) Crear el Codespace con el SDK ya incluido.** Al crear el Codespace, elige la configuración «con SDK de Google Cloud» (`.devcontainer/gcp/devcontainer.json`). Tarda más en crearse. Si tu Codespace ya existe, usa la forma a) en vez de reconstruirlo.

# B · Conectarte a Google Cloud

## 1. Iniciar sesión

**En tu equipo (Windows), con navegador:**

```
gcloud auth login
```

Se abre el navegador: elige tu cuenta y acepta. **Qué debes ver:** en el terminal, «You are now logged in as» seguido de tu cuenta.
**Si el navegador no se abre:** copia la dirección que imprime el terminal y ábrela a mano en el navegador, o usa la variante sin navegador de abajo.

**En el Codespace (no hay navegador propio):**

```
gcloud auth login --no-launch-browser
```

Sigue las instrucciones que imprime el terminal. Según la versión de `gcloud`, este flujo te pide abrir una dirección y pegar un código de vuelta, o ejecutar un comando en otro equipo que ya tenga `gcloud`. **La opción exacta se confirma con `gcloud auth login --help` y en T36 (sin verificar).** Pega el código de verificación **solo** en el terminal que te lo pidió.

## 2. Elegir proyecto y región por defecto

El identificador del proyecto te lo da el instructor (no uses el de otra persona).

```
gcloud config set project ID_DEL_PROYECTO
gcloud config set compute/region REGION
```

Sustituye `ID_DEL_PROYECTO` y `REGION` por los valores del curso (los indica el instructor; no los adivines). **Qué debes ver:** «Updated property [core/project]».
**Si falla** (permiso denegado o proyecto inexistente): revisa que escribiste bien el identificador y que iniciaste sesión con la cuenta correcta (paso 3).

## 3. Comprobar quién eres y cómo está configurado

```
gcloud auth list
gcloud config list
```

**Qué debes ver:** tu cuenta con un asterisco (`*`) como activa, y `project` (y la región) con los valores que fijaste. **Si falla:** si `auth list` sale vacío, vuelve al paso 1.

## 4. Comprobar que la conexión funciona, sin crear nada

```
gcloud projects describe ID_DEL_PROYECTO
```

Es solo de lectura. **Qué debes ver:** datos del proyecto (nombre, `projectId`, estado `ACTIVE`). **Si falla:** con «PERMISSION_DENIED» tu cuenta no tiene acceso a ese proyecto: avisa al instructor. Con «API not enabled» pide a quien administre el proyecto que lo revise. Si pregunta por facturación, no la actives por tu cuenta.

## 5. Cerrar sesión (al terminar siempre, y en equipos compartidos)

```
gcloud auth revoke
```

**Qué debes ver:** «Revoked credentials» con tu cuenta; después `gcloud auth list` sale sin cuentas. En el Codespace, además, **para y borra el Codespace** al acabar (la guía de Codespaces explica cómo): borrarlo elimina también las credenciales guardadas dentro.

# C · Extensiones de VS Code útiles

- **Cloud Code** (Google Cloud Code, de Google): ayuda a explorar y desplegar desde VS Code. **Sin verificar:** no se ha comprobado su identificador exacto ni su funcionamiento en el Codespace. Búscala por nombre en el panel de extensiones y comprueba que el editor sea Google. **No es necesaria** para la demo: todo se hace con `gcloud` en el terminal.
- Las que ya trae el Codespace del curso (Docker, Kubernetes, Python, Jupyter) bastan para S3.

# D · Resumen de «si falla»

| Síntoma | Qué probar |
|---|---|
| `gcloud` no se reconoce (Windows) | Cerrar VS Code del todo y abrirlo; reiniciar el equipo |
| El navegador no se abre | Copiar la dirección del terminal o usar `--no-launch-browser` |
| `PERMISSION_DENIED` | Cuenta equivocada (`gcloud auth list`) o sin acceso: avisar al instructor |
| El script del Codespace falla | Repetirlo (es repetible); si es de red, esperar y reintentar |
| No tengo facturación | Recorrido sin nube de la guía de migración |
