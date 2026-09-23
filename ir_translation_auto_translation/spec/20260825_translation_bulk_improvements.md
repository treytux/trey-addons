# Mejoras del asistente de traducción masiva

## Alcance aprobado

Ampliar el asistente `translation_bulk` para localizar objetos con campos
pendientes de traducción, reintentar errores de forma selectiva y presentar el
resumen sin saturar la pantalla con el detalle completo de errores.

## Filtro de objetos con campos pendientes

El filtro `translation_needed` localiza objetos que tengan alguno de los
campos seleccionados sin traducir correctamente en alguno de los idiomas
destino. Un objeto queda pendiente cuando:

- no existe una traducción almacenada para el idioma destino; o
- la traducción almacenada coincide con el valor del idioma origen.

Los campos cuyo valor origen está vacío no se consideran pendientes. La
consulta exige además que un idioma origen distinto de `en_US` exista de forma
explícita, evitando confundir el fallback de Odoo con una traducción real.

### Cambios realizados

- Añadir el valor `translation_needed` a `filter_type`.
- Añadir `record_needs_translation()` y
  `find_records_needing_translation()` al helper.
- Añadir `candidate_count` y `search_done` al wizard.
- Añadir `action_find_records_needing_translation()` para buscar, contar y
  preparar los IDs encontrados para la traducción.
- Añadir el botón **Find Objects**.
- Habilitar **Start Translation** solo tras completar la búsqueda y cuando
  existan objetos candidatos.
- Reiniciar la búsqueda cuando cambien modelo, campos o idiomas.

## Reintento de traducciones con errores

El helper procesa cada combinación de registro y campo dentro de un
`savepoint`. Los errores se conservan de forma estructurada para reintentar
solo las traducciones afectadas.

### Cambios realizados

- Añadir `error_items` al resumen de `translate_records_batch()`, incluyendo
  `record_id`, `field_name` y el mensaje.
- Añadir `failed_translation_data` al wizard para conservar los errores y su
  idioma destino en JSON.
- Añadir `action_retry_failed_translations()`.
- Añadir el botón **Retry Failed Translations**, visible solo cuando existen
  errores pendientes.
- Mantener los errores que continúen fallando y eliminar del listado los que
  se resuelvan o se omitan por existir ya una traducción.

## Resumen y detalle de errores

- Mantener en el resumen visible los totales de registros, campos, idiomas,
  éxitos, omisiones y errores.
- Separar el detalle en el campo técnico `error_log`.
- Mostrarlo dentro de un elemento `<details>` con el título **Error Summary**,
  cerrado inicialmente y desplegable al hacer clic.
- Mantener el detalle disponible después de una ejecución o reintento sin
  alterar la información utilizada por el botón de reintento.

## Áreas impactadas

- Backend:
  - `models/ir_translation_helper.py`
  - `wizards/ir_translation_bulk.py`
- Vistas:
  - `wizards/translation_bulk.xml`
- Tests:
  - `tests/test_ir_translation_auto_translation.py`
- Seguridad y datos:
  - Sin cambios en ACL, modelos ni tablas nuevas.

## Comportamiento esperado

1. El usuario selecciona el filtro de objetos con campos pendientes.
2. Ejecuta la búsqueda y revisa el número de candidatos.
3. Inicia la traducción únicamente sobre los IDs encontrados.
4. El asistente muestra los contadores del resultado.
5. Si existen errores, aparecen en **Error Summary** y se habilita el botón de
   reintento selectivo.

## Plan de pruebas

```bash
python3 -m py_compile \
  models/ir_translation_helper.py \
  wizards/ir_translation_bulk.py \
  tests/test_ir_translation_auto_translation.py
python3 -c "from lxml import etree; etree.parse('wizards/translation_bulk.xml')"
git diff --check
```

No se modifican automáticamente traducciones existentes salvo que el usuario
active `overwrite_existing`.
