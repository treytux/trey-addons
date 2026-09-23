# Traduccion de nombres de modelos

## Alcance aprobado

Revisar y completar las traducciones del modulo
`ir_translation_auto_translation` porque faltan terminos traducidos en la
definicion de modelos.

## Contexto tecnico

La exportacion de traducciones muestra dos modelos abstractos con nombres
tecnicos como cadena fuente:

- `ir.translatable.mixin`
- `ir.translation.helper`

Esto ocurre porque los modelos no declaran `_description`. Odoo utiliza el
nombre tecnico del modelo como descripcion y lo exporta a `ir.model`.

Tambien existe una traduccion marcada como `fuzzy` para `Product Variant`, que
quedo como `Producto` en vez de `Variante de producto`.

Ademas, las etiquetas devueltas por `_get_models()` en el asistente de
traduccion masiva no aparecen en los ficheros de traduccion porque la
seleccion es dinamica y sus literales no estaban marcados explicitamente con
`_()`.

## Cambios previstos

- Anadir `_description` en ingles a los modelos abstractos:
  - `Translatable Mixin`
  - `Translation Helper`
- Regenerar las traducciones del modulo.
- Traducir al espanol los nuevos nombres de modelo.
- Marcar como traducibles con `_()` las etiquetas de modelos soportados por
  el asistente de traduccion masiva.
- Eliminar marcas `fuzzy` y completar terminos de modelo/campo pendientes.
- Incrementar la version del manifiesto a `16.0.1.3.0`, al requerir
  actualizacion del modulo para aplicar metadatos y traducciones.

## Areas impactadas

- Backend: solo metadatos `_description` de modelos abstractos.
- Seguridad: sin cambios.
- Datos: metadatos `ir.model` y traducciones actualizados con `-u`.
- i18n: `i18n/es.po` e `i18n/ir_translation_auto_translation.pot`.

## Plan de pruebas

- Validar formato de traducciones:

  ```bash
  msgfmt --check i18n/es.po -o /tmp/ir_translation_auto_translation_es.mo
  ```

- Actualizar el modulo:

  ```bash
  oo exec mit16_260608 -u ir_translation_auto_translation --stop-after-init
  ```

- Comprobar que no quedan entradas `fuzzy` ni nombres tecnicos de modelos en
  la traduccion espanola.

## Riesgos y notas

- No se modifica logica de traduccion automatica.
- Los cambios de `_description` solo afectan a nombres visibles en metadatos y
  exportacion de traducciones.
