# S3 · presentación (estado)

**Estado a 20/11/2026: vacía a propósito.** Con el cambio de plan, las presentaciones de S3 son los cuatro laboratorios (`../laboratorio-recap-s2/`, `../laboratorio-mlflow/`, `../laboratorio-github-actions/`, `../laboratorio-red-neuronal/`). Lo de abajo es del plan previo (presentación de la migración a GCP, tarea T14 de `00-Planificacion/s3/TAREAS-S3.md`), que pasa a S4.

## Qué reutilizar de S2 (localizado en T01; nada de esto se ha ejecutado para S3 todavía)
- **Marco, paleta, teclas y reloj:** `01-Sesiones/S2-API-y-Docker/contenedores/marco.py` reutiliza el CSS y el JavaScript de
  `03-Entorno/guia-codespaces/generar.py`; `01-Sesiones/S2-API-y-Docker/del-ordenador-al-servicio/generar.py` genera un `index.html`
  con diapositivas `<section class="slide" data-part data-title data-min data-notes>` (parte, título, minutos y notas del ponente).
- **Pruebas que se copian y adaptan:**
  `del-ordenador-al-servicio/pruebas/test_presentacion.py` (esta al día con el generador; cada diapositiva con título, parte, minutos
  y notas de más de 80 caracteres; las órdenes citadas existen en el proyecto; sin recursos externos) y
  `contenedores/pruebas/test_contenedores.py` (los minutos declarados son la suma de los de cada paso; número e identificadores de diapositivas;
  enlaces relativos que resuelven; «sin probar» donde corresponde).
- **Minutos:** S3 debe sumar 240 (la prueba de S2 comprueba un rango de minutos propio de esa presentación: hay que ajustarla, no copiarla tal cual).
- **Aspecto (nada fuera del marco a 1280 × 720):** se revisa en un navegador real; no lo vigila ninguna prueba automática.

Otras carpetas de la sesión (`teoria/`, `practica/`, `tarea/`, `evidencias/`) las rellenan T02, T13, T17. `practica/ensayo-local/` ya tiene las salidas
reales del ensayo local de la migración (T05).