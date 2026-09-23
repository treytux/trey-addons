# Correccion de traduccion HTML en website_description

## Alcance aprobado

Analizar y corregir el problema detectado en el asistente de traduccion
automatica del modulo `ir_translation_auto_translation` para campos HTML
traducibles mediante `html_translate`, empezando por
`product.template.website_description`.

El caso reportado ocurre en la base `mit16_260608`: al traducir desde espanol a
ingles con sobrescritura activada, el valor traducido al ingles queda tambien
asignado al resto de idiomas visibles, como espanol y aleman por fallback.

## Diagnostico tecnico

`product.template.website_description` se define en `website_sale` como
`fields.Html(..., translate=html_translate)`.

En Odoo 16 este tipo de campo se almacena como `jsonb`, igual que otros campos
traducibles, pero no se debe actualizar igual que un campo con
`translate=True`.

El helper actual usa:

```python
record.with_context(lang=dest_lang).write({field_name: translated_text})
```

Esta escritura es valida para campos traducibles simples, pero para campos con
`translate` callable Odoo interpreta el HTML completo como nuevo contenido
estructural del idioma activo y sincroniza los terminos con los demas idiomas.
La reproduccion en `mit16_260608` confirma:

- Crear `website_description` en `es_ES` guarda el mismo valor en `en_US` y
  `es_ES` si no existia traduccion previa.
- Escribir el HTML completo en `en_US` con `write()` cambia tambien `es_ES`.
- Usar `update_field_translations()` con el diccionario de terminos conserva
  `es_ES` y actualiza solo `en_US`.

## Cambios previstos

- Detectar en `ir.translation.helper.translate_field_for_record()` si el campo
  seleccionado usa traduccion callable (`field.translate` callable).
- Para campos callable, traducir por terminos:
  - Leer el valor fuente con `with_context(lang=src_lang)`.
  - Extraer terminos traducibles con `field.get_trans_terms(source_text)`.
  - Traducir cada termino desde `src_lang` hacia `dest_lang`.
  - Aplicar el resultado con `record.update_field_translations()`.
- Mantener la ruta actual de `write()` para campos traducibles simples.
- Pasar `html=True` al proveedor cuando el campo sea HTML, o asegurar que los
  terminos se traduzcan como texto cuando Odoo ya haya extraido el texto plano.
- Mejorar la deteccion de traducciones existentes para campos callable para que
  `overwrite=False` siga respetando traducciones manuales.
- Anadir pruebas de regresion para `website_description` y campos HTML con
  `html_translate`.

## Areas impactadas

- Backend:
  - `models/ir_translation_helper.py`
  - Posibles ajustes menores en providers si se decide usar el parametro
    `html`.
- Tests:
  - `tests/test_ir_translation_auto_translation.py`
- Frontend:
  - Sin cambios previstos.
- Seguridad:
  - Sin cambios previstos.
- i18n:
  - No se esperan textos nuevos de usuario si los mensajes existentes no
    cambian.

## Plan de implementacion

### Fase 1: congelar especificacion

- Confirmar que el fix aplica a todos los campos con `translate` callable, no
  solo a `website_description`.
- Mantener el alcance dentro de `ir_translation_auto_translation`.

### Fase 2: backend

- Implementar una ruta privada para traducciones callable, por ejemplo
  `_translate_callable_field_for_record()`.
- Construir el diccionario esperado por Odoo:

  ```python
  {dest_lang: {source_term: translated_term}}
  ```

- Invocar `record.update_field_translations(field_name, translations)`.
- Conservar los contadores actuales de exito, omitidos y errores.

### Fase 3: frontend

- No aplica salvo que QA detecte que el wizard necesita explicar algun nuevo
  estado o restriccion.

### Fase 4: QA y pruebas automaticas

- Crear una prueba que reproduzca el fallo actual:
  - Crear un producto con `website_description` en `es_ES`.
  - Traducir `website_description` a `en_US` con overwrite.
  - Verificar que `en_US` cambia a la traduccion.
  - Verificar que `es_ES` conserva el texto original.
- Crear una prueba de `overwrite=False` en campo callable.
- Mantener pruebas existentes para `name` y `description`.

### Fase 5: i18n y comprobaciones finales

- Si no hay cadenas nuevas, no actualizar `i18n/*.po`.
- Si se cambian mensajes de error/log visibles, regenerar traducciones y
  revisar `i18n/GLOSSARY.md` si existe en el modulo.

## Plan de pruebas

Validacion automatica del modulo:

```bash
oo exec mit16_260608 -u ir_translation_auto_translation \
  --test-enable --stop-after-init
```

Validacion manual sugerida:

```bash
oo shell mit16_260608
```

En shell:

- Crear o seleccionar un `product.template`.
- Establecer `website_description` en `es_ES`.
- Lanzar el helper hacia `en_US` con overwrite.
- Revisar que el JSON de `product_template.website_description` mantiene claves
  diferentes para `es_ES` y `en_US`.

Consulta SQL de apoyo:

```sql
select id, website_description
from product_template
where id = <product_id>;
```

## Delegacion prevista

### Backend

- Tocar `models/ir_translation_helper.py`.
- Implementar escritura por terminos para campos con `translate` callable.
- Mantener compatibilidad con campos `char`, `text` y `html` traducibles
  simples.
- Riesgo principal: campos HTML con estructura distinta entre idiomas.

### QA

- Tocar `tests/test_ir_translation_auto_translation.py`.
- Anadir prueba de regresion sobre `product.template.website_description`.
- Verificar que los contadores del batch no cambian de significado.
- Ejecutar el comando de test del modulo.

### i18n

- Revisar solo si aparecen nuevas cadenas visibles.
- Si aplica, actualizar `i18n/es.po` y `i18n/ir_translation_auto_translation.pot`.

## Riesgos y notas

- `website_description` hereda comportamiento nativo de Odoo: si se crea el
  campo por primera vez en un idioma no ingles, Odoo puede inicializar tambien
  `en_US` con el mismo valor como fallback.
- El fix no debe intentar modificar Odoo core ni `website_sale`.
- El proveedor externo puede devolver el texto original si falla; eso debe
  seguir contandose como exito solo si la llamada no falla, respetando el
  comportamiento actual.
- El bug puede afectar a otros campos `fields.Html` con
  `translate=html_translate`, por lo que la solucion debe ser generica para
  campos callable.

## Implementacion realizada

- `ir.translation.helper` detecta campos con `translate` callable.
- Los campos callable se actualizan con `record.update_field_translations()`
  usando un diccionario de terminos, evitando escrituras completas con
  `with_context(lang=dest_lang).write()`.
- La ruta anterior se mantiene para campos traducibles simples.
- `overwrite=False` en campos callable revisa las traducciones almacenadas y
  no confunde el fallback de otro idioma con una traduccion real del destino.
- Se anadieron pruebas `post_install` para `website_description`, porque el
  campo pertenece a `website_sale` y puede no estar disponible durante las
  pruebas `at_install` del modulo.
- Las pruebas que traducen campos callable hacia `es_ES` verifican que el
  idioma este instalado antes de ejecutar la asercion, porque
  `update_field_translations()` rechaza idiomas no activados.
- La version del modulo queda en `16.0.1.3.1`, al ser un cambio Python de
  reinicio sin cambios de esquema ni datos.

## Validacion realizada

- Validacion focalizada en `mit16_260608` con `oo shell` y rollback:
  - Crear producto temporal con `website_description` en `es_ES`.
  - Traducir a `en_US` mediante el helper.
  - Confirmar que `en_US` recibe la traduccion.
  - Confirmar que `es_ES` conserva el texto original.
- Validacion automatica acotada:

  ```bash
  oo exec mit16_260608 --test-enable \
    --test-tags /ir_translation_auto_translation --stop-after-init
  ```

  Resultado: 0 fallos y 0 errores. Se ejecutaron tambien las 2 pruebas
  `post_install` de `TestCallableHtmlTranslation`.
- Validacion sintactica con `ast.parse` sobre los ficheros Python tocados:
  correcta.
- `pre-commit run --files ...` no pudo ejecutarse porque `pre-commit` no
  detecta este directorio como repositorio Git en el entorno actual.
- La ejecucion de `oo exec mit16_260608 -u ir_translation_auto_translation
  --test-enable --stop-after-init` arranca y ejecuta las pruebas `at_install`
  del modulo, pero la carga posterior de la base queda bloqueada por un error
  ajeno en `mercadoit_customize/views/helpdesk_ticket_views.xml`, donde no se
  encuentra el xpath sobre `product_id` en la vista padre de `helpdesk.ticket`.
