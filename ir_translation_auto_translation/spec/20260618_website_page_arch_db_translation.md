# Correccion de traduccion del contenido de paginas web

## Alcance aprobado

Corregir el error al traducir en bloque el modelo `website.page` cuando se
selecciona el campo mostrado como blob de contenido de pagina en la base
`mit16_260615`.

El fallo aparece con `website.page.arch_db`, campo relacionado con
`view_id.arch_db`, mientras que otros campos SEO relacionados funcionan porque
usan traduccion simple.

## Diagnostico tecnico

`website.page.arch_db` se muestra como `Arch Blob` y almacena el contenido XML
real en `ir.ui.view.arch_db`.

En `mit16_260615`, la pagina `/sobre-gote` corresponde a `website.page` 75 y
`ir.ui.view` 13387. El sitio GOTE tiene idioma por defecto `es_ES`, pero
`arch_db` mantiene claves JSONB `en_US` y `es_ES`. En esta pagina ambas claves
pueden contener inicialmente texto espanol porque `en_US` actua como fallback
tecnico de Odoo, no necesariamente como contenido ingles real.

El asistente usa `ir.translation.helper` para traducir campos con
`translate` callable mediante terminos. En esa ruta se llama directamente a
`field._get_stored_translations(record)`.

Para `website.page.arch_db`, `record` es un `website.page`, pero el campo
almacenado esta en `ir.ui.view`. Esa lectura intenta consultar `arch_db` sobre
la tabla `website_page`, deja la transaccion abortada y despues falla tambien
la escritura de `status_log` del wizard con `InFailedSqlTransaction`.

Ademas, cuando el origen real es `es_ES` y el destino es `en_US`, una copia
destino identica al origen no debe considerarse una traduccion existente. El
idioma origen debe ser de solo lectura durante toda la traduccion: si una
operacion cambia el valor de `source_lang`, la traduccion debe fallar y
revertirse dentro del savepoint.

## Cambios previstos

- Resolver el registro y campo almacenado real antes de leer traducciones de
  campos callable relacionados.
- Escribir campos callable sobre el registro almacenado real con
  `update_field_translations()` y enviando solo la clave del idioma destino.
- Saltar traducciones donde idioma origen e idioma destino sean el mismo.
- No considerar traduccion existente una copia del destino identica al origen
  cuando los idiomas son distintos.
- Comprobar despues de cada traduccion que el idioma origen conserva el mismo
  valor que tenia al inicio; si cambia, lanzar error para revertir el
  savepoint.
- Proteger cada traduccion de campo con un savepoint para que errores SQL por
  un registro no aborten toda la transaccion del wizard.
- Anadir pruebas de regresion para campos simples, HTML callable y
  `website.page.arch_db`, garantizando que solo cambian los idiomas destino.
- Anadir una accion masiva en el menu **Accion** de la vista listado de
  `website.page` para abrir el asistente de traduccion en bloque con las
  paginas seleccionadas.

## Areas impactadas

- Backend:
  - `models/ir_translation_helper.py`
- Datos / UI:
  - `data/actions_data.xml`
- Tests:
  - `tests/test_ir_translation_auto_translation.py`
- Frontend:
  - Sin cambios.
- Seguridad:
  - Sin cambios.
- i18n:
  - No se preven cadenas nuevas de usuario.

## Plan de pruebas

Validacion automatica del modulo:

```bash
oo exec mit16_260615 -u ir_translation_auto_translation \
  --test-enable --stop-after-init
```

Validacion manual:

- Abrir el asistente de traduccion en bloque.
- Seleccionar modelo `website.page`.
- Seleccionar el campo `Arch Blob` / blob de contenido.
- Traducir a un idioma destino.
- Confirmar que no se produce RPC error y que el contenido se guarda solo en
  la traduccion del idioma destino.
- Confirmar que el valor de `arch_db` en el idioma origen queda identico al
  valor previo a la traduccion.
- Abrir Sitio web > Paginas, seleccionar una o varias paginas y confirmar que
  el menu **Accion** muestra **Bulk Translate**.
