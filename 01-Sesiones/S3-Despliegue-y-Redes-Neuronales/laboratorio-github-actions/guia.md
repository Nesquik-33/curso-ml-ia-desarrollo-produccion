# Laboratorio de GitHub Actions: romper y arreglar (S3 · 90 min)

En tu copia del repositorio del curso (tu *fork*) y desde tu Codespace vas a:

1. crear una rama `lab/actions-s3`;
2. añadir un *workflow* que ejecuta las pruebas del proyecto cada vez que haces `git push`;
3. verlo **en verde** en la pestaña **Actions**;
4. **romper** una prueba a propósito (un cambio de una línea) → **rojo**, leer el registro y encontrar el fallo;
5. **arreglarlo** (sin borrar la prueba) → **verde** otra vez.

Publicar imágenes y desplegar **no** es de hoy: es de S4. Hoy no se usa Google Cloud.

Presentación: [`index.html`](index.html) (cada orden se copia con **⧉**). Workflow listo para copiar: [`pruebas-proyecto.yml`](pruebas-proyecto.yml).

> **Estado de validación.** El workflow, la rotura y el arreglo se comprobaron en local (la prueba que se rompe falla con el cambio y pasa sin él). El recorrido completo (verde · rojo · verde) se hizo el 20/11/2026 en el Codespace del profesor y en GitHub: son las capturas de la presentación. Duración de un run en GitHub: 1 min 16 s el primero y 51 s – 1 min 6 s con la caché de pip. Lo que no se pudo ver (el aviso para activar Actions en un fork nuevo) sigue marcado **(sin verificar)**.

---

## 1. Qué es CI y por qué (en un minuto)

**CI** (*Continuous Integration*, integración continua) es una costumbre: **cada cambio que subes se comprueba solo**, en una máquina limpia, con las mismas órdenes de siempre. Si algo se rompe, lo sabes en minutos y sabes **qué cambio** lo rompió.

- Sin CI: «en mi máquina funciona»; las pruebas se pasan cuando alguien se acuerda.
- Con CI: cada `git push` deja un resultado **verde** (todo bien) o **rojo** (algo falló), con su registro, visible para todo el equipo.

**GitHub Actions** es el servicio de GitHub que hace esto. Vocabulario mínimo:

| Palabra | Qué es |
|---|---|
| *workflow* | un archivo YAML en `.github/workflows/` que dice **cuándo** y **qué** ejecutar |
| disparador (`on:`) | el suceso que lo pone en marcha: un `push`, un *pull request*, un botón… |
| *runner* | la máquina (aquí, Linux nueva y vacía) que presta GitHub para ejecutarlo |
| *job* | un trabajo dentro del workflow; corre en un *runner* |
| *step* (paso) | cada orden o acción del *job*, en orden; si uno falla, el *job* se para en rojo |
| *run* (ejecución) | una vez concreta que se ejecutó el workflow, con su registro |

## 2. Anatomía del YAML, línea a línea

```yaml
name: Pruebas del proyecto

on:
  push:
    branches: ['lab/**']
  workflow_dispatch:

permissions:
  contents: read

jobs:
  pruebas:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults:
      run:
        working-directory: 04-Proyecto-Base
    env:
      CURSO_SIN_PANTALLA: "1"
    steps:
      - name: Descargar el repositorio
        uses: actions/checkout@v4

      - name: Preparar Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: 04-Proyecto-Base/requirements-*.txt

      - name: Instalar dependencias
        run: |
          pip install -r requirements-dev.txt
          pip install -e . --no-deps

      - name: Ejecutar las pruebas
        run: python -m pytest -v tests/test_raw_y_master.py tests/test_fs_y_ml.py tests/test_interfaz.py
```

(El archivo [`pruebas-proyecto.yml`](pruebas-proyecto.yml) es este mismo, con comentarios.)

| Línea | Qué hace |
|---|---|
| `name:` | el nombre que verás en la pestaña Actions |
| `on: push: branches: ['lab/**']` | se dispara con cada `push` a una rama que empiece por `lab/`. `develop` y `main` **no** lo disparan |
| `workflow_dispatch:` | añade un botón para lanzarlo a mano. GitHub solo muestra ese botón cuando el archivo está en la rama principal: hoy no lo usaremos |
| `permissions: contents: read` | el workflow solo puede **leer** el repositorio. Principio de mínimo privilegio |
| `jobs: pruebas:` | un único *job* llamado `pruebas` |
| `runs-on: ubuntu-latest` | corre en una máquina Linux nueva de GitHub: no hay nada instalado de tu Codespace |
| `timeout-minutes: 10` | si algo se cuelga, se corta a los 10 minutos (por defecto serían horas) |
| `working-directory: 04-Proyecto-Base` | todas las órdenes `run:` se ejecutan dentro de la carpeta del proyecto |
| `env: CURSO_SIN_PANTALLA: "1"` | variable de entorno del proyecto: dibuja gráficos sin ventana |
| `uses: actions/checkout@v4` | una **acción** ya hecha: descarga tu repositorio en el *runner* |
| `uses: actions/setup-python@v5` | instala Python 3.11; `cache: pip` guarda los paquetes descargados para que el siguiente run vaya más rápido |
| `pip install -r requirements-dev.txt` | las mismas versiones que el entorno del curso (es lo que instala también el workflow `validar-dos-contenedores.yml` del curso) |
| `pip install -e . --no-deps` | instala el paquete `ia_mlops` del proyecto |
| `python -m pytest -v …` | las pruebas. Si alguna falla, `pytest` termina con error, el paso se pone en rojo y el run también |

**Por qué esas tres pruebas.** No necesitan datos descargados ni ejecutar antes el pipeline: `tests/conftest.py` construye la base operacional y la analítica desde la **muestra** que ya está en el repositorio (`data/raw/muestra_online_retail_ii.csv`). Tampoco necesitan Docker ni ejecutar cuadernos (las pruebas de cuadernos están marcadas `lento`).

| Archivo | Qué comprueba |
|---|---|
| `tests/test_raw_y_master.py` | la ingesta: capas RAW y MASTER |
| `tests/test_fs_y_ml.py` | las variables (FS) y el conjunto para el modelo (ML), por fecha de corte |
| `tests/test_interfaz.py` | la interfaz de consulta de S2: ids → variables → modelo → recomendación, y la **regla de negocio** de tramos |

**No choca con los workflows del curso.** `validar-dos-contenedores.yml` solo se dispara con `push` a `develop`; `validar-codespace.yml`, solo con *pull requests*; `validar-windows.yml`, solo si el cambio toca `03-Entorno/`. En la rama `lab/actions-s3` solo debería aparecer **Pruebas del proyecto** (compruébalo en la pestaña Actions).

## 3. Preparar el fork y el Codespace

1. **Fork.** Si aún no tienes tu copia del repositorio del curso en tu cuenta de GitHub, créala con el botón **Fork** del repositorio del curso. El laboratorio se hace **en tu fork**: los *runs* se ejecutan en tu cuenta.
2. **Codespace.** Abre un Codespace **de tu fork**, en la rama `develop`. Trabaja desde la carpeta raíz: `/workspaces/<nombre-de-tu-repositorio>`.
3. **Actions en el fork.** En los forks, GitHub puede tener Actions desactivado al principio. Entra en la pestaña **Actions** de tu fork: **si ves un aviso** que pide activar los workflows, acéptalo (el texto exacto del botón: **sin verificar**). Si no ves aviso, no hay que hacer nada.
4. **Comprueba que estás al día y en `develop`:**

```bash
git switch develop
git pull
git status
```

## 4. Paso a paso

### Paso 1 · Rama y archivo del workflow (captura `a01-rama`)

```bash
git switch -c lab/actions-s3
mkdir -p .github/workflows
cp 01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-github-actions/pruebas-proyecto.yml .github/workflows/
git status
```

Si tu fork no tiene todavía esa carpeta del curso, crea el archivo pegando el YAML: abre el editor con `code .github/workflows/pruebas-proyecto.yml`, pega el YAML de la sección 2 y guarda.

**Qué debes ver:** `git status` dice que estás en `lab/actions-s3` y muestra `.github/` como archivo nuevo sin seguimiento.

### Paso 2 · Míralo en el editor (captura `a02-yaml`)

```bash
code .github/workflows/pruebas-proyecto.yml
```

**Qué debes ver:** el YAML con su sangría. En YAML **la sangría es la sintaxis**: dos espacios por nivel, nunca tabuladores.

### Paso 3 · Commit y push (captura `a03-push`)

```bash
git add .github/workflows/pruebas-proyecto.yml
git commit -m "Laboratorio S3: workflow que ejecuta las pruebas del proyecto"
git push -u origin lab/actions-s3
```

**Qué debes ver:** git crea la rama en GitHub (`-u` la deja enlazada: los siguientes `git push` ya no necesitan nombre).

**Si falla:** si git pide nombre y correo, configúralos una vez con `git config user.name "Tu nombre"` y `git config user.email "tu-correo"` y repite el commit.

### Paso 4 · La pestaña Actions (capturas `a04-actions-lista`, `a05-run-curso`, `a06-run-verde`)

En tu fork, pestaña **Actions**: aparece un *run* de **Pruebas del proyecto** con el mensaje de tu commit y la rama `lab/actions-s3`; mientras corre, un círculo amarillo e *In progress*. Entra en él y luego en el *job* `pruebas`: verás los pasos en orden mientras se ejecutan.

**Qué debes ver:** todos los pasos con su marca verde y, dentro de **Ejecutar las pruebas**, una línea `PASSED` por prueba y al final el resumen `passed`. La primera vez tarda más (descarga paquetes); con la caché de pip, menos. Duración real el 20/11/2026: 1 min 16 s el primer run (instalar dependencias 46 s, pruebas 12 s, «45 passed»).

**Si falla:**
- No aparece ningún run: ¿el archivo está en `.github/workflows/` (con punto) en la **raíz** del repositorio? ¿La rama empieza por `lab/`? ¿Actions está activado en tu fork (paso 3 de la sección 3)?
- Error de YAML (el run falla sin llegar a los pasos): revisa la sangría.

### Paso 5 · Romper a propósito (captura `a07-rotura`)

La regla de negocio de la interfaz de S2 está en `04-Proyecto-Base/ia_mlops/config.py` (`SEGMENTOS_RECOMPRA`): un cliente es **alta** desde una probabilidad de **0,70**. Vamos a subir ese umbral a 0,75 sin avisar a la prueba:

```bash
sed -i "s/'desde': 0.70/'desde': 0.75/" 04-Proyecto-Base/ia_mlops/config.py
git diff
git commit -am "Rotura a propósito: el tramo alta empieza en 0,75"
git push
```

**Qué debes ver:** `git diff` enseña **una sola línea** cambiada (`- 'desde': 0.70` / `+ 'desde': 0.75`).

### Paso 6 · El run en rojo y el registro (capturas `a08-run-rojo`, `a09-log-error`)

En Actions aparece un run nuevo, esta vez **en rojo**. Entra, abre el paso **Ejecutar las pruebas** y busca `FAILED`:

```text
FAILED tests/test_interfaz.py::test_la_regla_de_negocio
E       AssertionError: assert ['alta', 'med...baja', 'baja'] == ['alta', 'alt...baja', 'baja']
E         At index 1 diff: 'media' != 'alta'
```

(Salida real de la misma prueba en local; en GitHub, con `-v`, pytest enseña además la lista completa.)

**Cómo leerlo:** la prueba pide que una probabilidad de **0,70** (la segunda de la lista, índice 1) sea `alta`; con el umbral en 0,75 sale `media`. El registro te dice **qué prueba**, **en qué línea** y **qué esperaba frente a qué obtuvo**. Las demás pruebas siguen en `PASSED`: el fallo está acotado.

**La pregunta importante:** ¿está mal la prueba o está mal el cambio? Aquí el umbral es una **regla de negocio acordada**: el cambio no estaba acordado, así que se arregla el código, **no se borra ni se retoca la prueba**.

### Paso 7 · Arreglar (captura `a10-arreglo`)

```bash
git revert --no-edit HEAD
git log --oneline -3
git push
```

`git revert` crea un commit **nuevo** que deshace el anterior: el historial conserva la rotura y su arreglo. (Alternativa: editar la línea a mano de vuelta a `0.70`, `git commit -am "…"` y `git push`.)

### Paso 8 · Verde otra vez y el historial (capturas `a11-run-verde-otra-vez`, `a12-historial`)

**Qué debes ver:** el run del *revert* en verde y, en la lista de runs de **Pruebas del proyecto**, la secuencia **verde · rojo · verde** con los tres mensajes de commit (#1, #2 y #3). Esa lista es la prueba de que cada cambio se comprobó.

## 5. Limpieza

Cuando acabes (y si ya no lo necesitas), borra la rama del laboratorio en GitHub y en tu Codespace:

```bash
git switch develop
git push origin --delete lab/actions-s3
git branch -D lab/actions-s3
```

Los runs ya ejecutados se quedan en la pestaña Actions como historial.

## 6. Puente a S4

Hoy el workflow solo **comprueba**. En S4 se le añade lo que lleva el modelo a producción:

- **Pipeline** raw → modelo y registro en MLflow dentro del workflow.
- **Construir y publicar la imagen** en Artifact Registry (Google Cloud).
- **Desplegar en Cloud Run con aprobación**: un paso que espera a que una persona autorizada lo apruebe (entornos protegidos de GitHub).
- **Autenticación con GCP sin claves**: *Workload Identity Federation*, en la que GitHub demuestra quién es con un token de corta duración y Google le da permisos solo para eso. Ninguna clave guardada en el repositorio.

La plantilla `04-Proyecto-Base/deploy/github-actions/ci.yml` del proyecto ya enseña el paso intermedio: pruebas más construir y probar la imagen.

## 7. Autoevaluación

1. ¿Qué dos líneas del YAML deciden **cuándo** se ejecuta el workflow? → `on: push: branches: ['lab/**']` (y `workflow_dispatch`).
2. ¿Por qué `permissions: contents: read`? → mínimo privilegio: el workflow no necesita escribir nada.
3. ¿Por qué el run es verde en el *runner* aunque ahí no hay tu entorno conda? → porque el workflow instala todo desde `requirements-dev.txt` en una máquina limpia; eso es justo lo que comprueba.
4. El run sale rojo: ¿dónde miras primero? → en el paso rojo, la línea `FAILED` y las líneas `E` de debajo.
5. ¿Por qué no se arregla borrando la prueba? → porque la prueba protege una regla acordada; borrarla oculta el problema.
