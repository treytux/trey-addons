# Soporte de traducción en bloque para publicaciones del blog

## Alcance aprobado

Permitir traducir, además de los modelos de datos actuales
(`product.template`, `product.product`, `product.public.category`,
`website.page`, `res.partner`), las entradas del blog (`blog.post`) para
MercadoIT.

Este cambio cubre:

- Registrar `blog.post` como modelo traducible mediante un nuevo archivo
  `models/blog_post.py`.
- Anadir `blog.post` al desplegable de modelos del asistente de traducción
  en bloque (`ir.translation.bulk.wizard`), inmediatamente despues de
  `website.page`, con la etiqueta `Blog Post Pages` (`Paginas de
  publicaciones de blog` en es_ES).
- Anadir la opcion **Traducción en bloque** al menu **Acción** del listado
  "Paginas de publicaciones de blog" (Sitio web > Sitio > Contenido >
  Publicaciones del blog), justo después de **Eliminar**, replicando el
  patron ya existente para `website.page`.

No forma parte de este alcance (se abordara en cambios posteriores, si se
solicitan):

- Cualquier cambio en la estructura del menu Sitio web > Sitio > Contenido
  en si mismo (no se anaden ni modifican `<menuitem>`).
- Actualización de `README.rst` con `blog.post` en la lista de modelos
  soportados.

## Diagnóstico técnico

El campo `model_name` de `ir.translation.bulk.wizard` es un `Selection`
cuyas opciones provienen de `_get_models()`
(`wizards/ir_translation_bulk.py`). Anadir un modelo nuevo al
asistente solo requiere una nueva tupla `(model, _('Etiqueta'))` en ese
método; el motor de traducción (`models/ir_translation_helper.py`) ya es
genérico y no necesita cambios, puesto que `website.page` funciona hoy sin
que su modelo herede ningún mixin de este addon.

El campo traducible relevante de `blog.post` es `content`
(`fields.Html(..., translate=html_translate)`, definido en
`website_blog/models/website_blog.py`), es decir, un campo con `translate`
"callable" del mismo tipo que `product.template.website_description`
(corregido en `spec/20260611_website_description_html_translation.md`) y
`website.page.arch_db` (corregido en
`spec/20260618_website_page_arch_db_translation.md`). El helper ya detecta
`callable(field.translate)` y usa `field.get_trans_terms()` +
`update_field_translations()`, por lo que `blog.post.content` queda
cubierto sin cambios adicionales. A diferencia de `website.page.arch_db`,
`content` es un campo `store=True` propio de `blog.post`, no un campo
`related` que resuelva a otro modelo, lo que simplifica el caso.

Se anade también un archivo `models/blog_post.py` que hereda
`ir.translatable.mixin` sobre `blog.post`, siguiendo el mismo patron mínimo
que `models/product_product.py`. Esto da acceso a
`action_open_translation_wizard()` para una futura accion de traducción
individual por registro y mantiene la consistencia con el resto de modelos
de producto ya cubiertos por el addon.

Como `blog.post` esta definido en el modulo `website_blog` (no instalado
por defecto como dependencia de este addon), heredarlo con `_inherit`
exige declarar `website_blog` en `depends` del manifest; en caso contrario
la carga del módulo fallaria si `website_blog` no estuviera ya instalado
antes.

Para el boton **Traducción en bloque** en el listado, se replica
exactamente el patron de `action_website_page_bulk_translate_server`: un
`ir.actions.server` con `binding_model_id` apuntando al modelo objetivo,
`binding_type='action'` y `binding_view_types='list'`, cuyo código abre
`ir.translation.bulk.wizard` con `default_model_name`, `active_ids` y
`active_model` tomados de los registros seleccionados en el listado
(`filter_type` se resuelve como `'selected'` automáticamente en
`default_get()` del wizard al detectar `active_ids`/`active_model` en el
contexto).

### Incidencia detectada durante la implementación

Al registrar `models/blog_post.py` en `models/__init__.py` siguiendo
estrictamente el orden alfabético, `blog_post` quedo importado **antes**
que `ir_translatable_mixin`. Odoo construye los modelos
(`Model._build_model`) en el mismo orden en que se importan sus clases; al
intentar construir `blog.post` (que hace `_inherit = ['blog.post',
'ir.translatable.mixin']`) el mixin `ir.translatable.mixin` aun no existía
en el registro, y la carga del módulo fallaba con:

```
TypeError: Model 'blog.post' inherits from non-existing model
'ir.translatable.mixin'.
```

Este fallo en la construcción del registro impedia también que se
registraran correctamente otros añadidos de este módulo (por ejemplo los
campos de `res.config.settings` como `translation_provider`), provocando
en el cliente web el error genérico "Missing field string information for
the field 'translation_provider' from the 'res.config.settings' model" en
Ajustes, sin relación aparente con `blog.post`.

Corrección: en `models/__init__.py`, `blog_post` debe importarse después
de `ir_translatable_mixin` (igual que ya ocurria con `product_product` y
`product_template`, que dependen del mismo mixin). El orden alfabético
estricto no es válido cuando existe una dependencia de herencia entre
modelos del mismo módulo.

## Cambios previstos

- `models/blog_post.py` (nuevo): `BlogPost(models.Model)` con
  `_name = 'blog.post'` y `_inherit = ['blog.post',
  'ir.translatable.mixin']`.
- `models/__init__.py`: importar `blog_post` despues de
  `ir_translatable_mixin` (no en orden alfabético estricto, por la
  dependencia de herencia del mixin).
- `wizards/ir_translation_bulk.py`: anadir
  `('blog.post', _('Blog Post Pages'))` en `_get_models()`, entre
  `website.page` y `res.partner`.
- `data/actions_data.xml`: nuevo registro `ir.actions.server`
  `action_blog_post_bulk_translate_server`, vinculado a
  `website_blog.model_blog_post`, con `binding_type='action'` y
  `binding_view_types='list'`, analogo a
  `action_website_page_bulk_translate_server`.
- `__manifest__.py`: anadir `website_blog` a `depends` y subir versión de
  `16.0.1.4.1` a `16.0.1.6.0` en dos pasos (`1.5.0` al registrar el modelo
  y la entrada del desplegable; `1.6.0` al anadir el nuevo registro de
  datos `ir.actions.server`); ambos cambios requieren `-u`.
- `i18n/es.po` e `i18n/ir_translation_auto_translation.pot`: anadir la
  entrada `msgid "Blog Post Pages"` / `msgstr "Paginas de publicaciones de
  blog"`; anadir la referencia a
  `action_blog_post_bulk_translate_server` en los comentarios de
  ubicación de la entrada existente `msgid "Bulk Translate"` (comparte
  cadena con las acciones de `product.template` y `website.page`).
- `tests/test_ir_translation_auto_translation.py`: nueva clase
  `TestBlogPostActions` con `test_blog_post_bulk_translate_server_action`,
  análoga a `TestWebsitePageActions`.

## Áreas impactadas

- Backend:
  - `models/blog_post.py` (nuevo)
  - `models/__init__.py`
  - `wizards/ir_translation_bulk.py`
  - `__manifest__.py`
- Datos / UI:
  - `data/actions_data.xml`
- Tests:
  - `tests/test_ir_translation_auto_translation.py`
    (`TestBlogPostActions`)
- Seguridad:
  - Sin cambios. El ACL de escritura sobre `blog.post` ya lo gestiona
    `website_blog` (requiere `website.group_website_designer` para
    escritura); `security/ir.model.access.csv` de este addon solo cubre
    sus propios modelos transitorios/abstractos.
- i18n:
  - `i18n/es.po`, `i18n/ir_translation_auto_translation.pot`.

## Plan de pruebas

Validación automática del modulo:

```bash
oo exec <db> -u ir_translation_auto_translation \
  --test-enable --stop-after-init
```

Validación manual:

- Ajustes > Traducciones > Traducción automatica > Traducir en bloque.
- Abrir el desplegable **Modelo** y confirmar que aparece **Páginas de
  publicaciones de blog** inmediatamente despues de **Pagina web** y
  antes de **Contacto**.
- Seleccionar `blog.post`, elegir el campo `content`, un idioma origen y
  uno o varios idiomas destino, y confirmar que la traducción se completa
  sin error RPC.
- Confirmar que el contenido del idioma origen no se modifica al
  traducir (mismo criterio de regresion aplicado en
  `spec/20260611_website_description_html_translation.md` y
  `spec/20260618_website_page_arch_db_translation.md`).
- Sitio web > Sitio > Contenido > Publicaciones del blog: seleccionar uno
  o varios registros del listado y confirmar que el menu **Accion**
  muestra **Traduccion en bloque** inmediatamente despues de
  **Eliminar**.
- Confirmar que al pulsar **Traducción en bloque** se abre el asistente
  con el modelo `blog.post` y los registros seleccionados ya precargados
  (`filter_type = 'selected'`), sin mostrar el desplegable de modelo.
- Confirmar que Ajustes (`res.config.settings`) carga sin el error
  "Missing field string information for the field 'translation_provider'"
  tras aplicar la correccion de orden de imports.
