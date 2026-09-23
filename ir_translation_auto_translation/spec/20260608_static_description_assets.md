# Presentacion del modulo en Apps

## Alcance aprobado

Corregir el modulo `ir_translation_auto_translation` para que incluya los
archivos de presentacion esperados por Odoo en `static/description/`.

## Contexto tecnico

El manifiesto del modulo ya declara la imagen
`static/description/banner.png`, pero el directorio `static/description/` no
existe. Tampoco estan versionados `index.html` ni `icon.png`, que forman parte
de la presentacion estandar de los modulos Trey en la vista de Apps.

El modulo vive en `addons/trey-addons/ir_translation_auto_translation`, dentro
del repositorio de addons Trey permitido para cambios. No se requieren cambios
en Odoo core, OCA ni repositorios de cliente.

## Cambios previstos

- Crear el directorio `static/description/`.
- Anadir `static/description/index.html` adaptado al modulo, con descripcion
  en espanol.
- Incluir en `index.html` la descripcion completa del README, la
  configuracion del modulo, el uso, modelos soportados, ejemplo y notas.
- Anadir `static/description/icon.png` reutilizando el icono estandar Trey de
  otro modulo cuando no exista un icono especifico aprobado.
- Anadir `static/description/banner.png`, ya referenciado en el manifiesto.
- Anadir los SVG complementarios `icon.svg` y `banner.svg` para mantener la
  estructura habitual de los modulos Trey.
- Incrementar la version del manifiesto a `16.0.1.2.1` al tratarse de un
  cambio de activos estaticos que solo requiere reinicio.

## Areas impactadas

- Backend: sin cambios de modelos, ORM ni logica Python.
- Frontend: solo activos de descripcion del modulo para Apps.
- Seguridad: sin cambios en ACL ni reglas.
- Datos: sin nuevos XML/CSV cargables por actualizacion.
- i18n: no se esperan cadenas Odoo nuevas; el `index.html` de descripcion se
  redacta en espanol y no requiere `i18n/*.po`.

## Plan de ejecucion

1. Crear `static/description/` en el modulo.
2. Copiar como base `index.html`, `icon.png` y `banner.png` desde un modulo
   Trey con estructura equivalente.
3. Adaptar `index.html` al nombre, resumen y funcionalidad real de Automatic
   Translation.
4. Verificar que las rutas declaradas por `__manifest__.py` existen.
5. Incrementar la version del manifiesto de `16.0.1.2.0` a `16.0.1.2.1`.
6. Revisar que no se han introducido cadenas Odoo traducibles nuevas.

## Plan de pruebas

- Validar existencia de archivos:

  ```bash
  test -f static/description/index.html
  test -f static/description/icon.png
  test -f static/description/banner.png
  test -f static/description/icon.svg
  test -f static/description/banner.svg
  ```

- Validar sintaxis HTML basica mediante inspeccion manual del fichero.
- Validacion funcional tras actualizar o reiniciar el entorno:

  ```bash
  oo exec mit16_260608 -u ir_translation_auto_translation --stop-after-init
  ```

- Abrir Apps en Odoo y comprobar que el modulo muestra icono, banner y
  descripcion sin errores de recurso faltante.

## Delegacion prevista

### Frontend

- Tocar solo `static/description/`.
- Reutilizar el estilo de `addons/trey-addons/mail_server_user_domain`.
- Adaptar el texto descriptivo a la funcionalidad del modulo.
- No modificar vistas backend ni assets web del modulo.

### QA

- Revisar que las rutas de imagen del manifiesto existen.
- Revisar que `index.html` usa una estructura coherente con otros modulos
  Trey.
- Confirmar que no hay cambios funcionales que requieran tests Python.

### i18n

- Sin tarea prevista salvo que durante la implementacion se anadan cadenas
  cargadas por Odoo fuera de `static/description/index.html`.

## Riesgos y notas

- Si el cliente quiere iconografia especifica para traduccion automatica, el
  icono estandar Trey deberia sustituirse por un activo aprobado.
- Al tratarse de archivos de presentacion, no se espera impacto funcional en
  traducciones automaticas ni en asistentes existentes.
