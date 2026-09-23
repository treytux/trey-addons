# Filtro por compañía en el asistente de traducción masiva

## Alcance

Añadir al asistente `translation_bulk` un filtro por compañía para limitar la
selección de registros de modelos que dispongan del campo `company_id`.

## Cambios realizados

- Añadir el campo `company_id` al asistente como `Many2one` hacia
  `res.company`.
- Seleccionar por defecto la compañía actual del usuario.
- Mostrar la compañía en modo solo lectura para que el usuario pueda
  verificarla sin modificar el ámbito de la traducción.
- Mostrar el filtro únicamente cuando el modelo elegido dispone de
  `company_id`.
- Aplicar el dominio de compañía a los filtros de todos los registros, dominio
  personalizado, registros seleccionados y objetos pendientes de traducción.
- Reiniciar la búsqueda de objetos pendientes cuando cambia la compañía.
- Mantener sin filtro adicional los modelos que no tienen `company_id`.

## Comportamiento esperado

Al abrir el asistente se selecciona automáticamente la compañía actual. Para
modelos como `product.template`, las búsquedas y traducciones solo consideran
los registros cuya compañía coincide con la seleccionada.

## Validación

Se comprueba que la compañía actual se establece como valor predeterminado y
que el dominio generado utiliza el campo `company_id` del modelo.

## Acceso desde categorías

- Mantener `product.public.category` en el listado de modelos disponibles.
- Añadir el mixin de traducción a `product.category` y
  `product.public.category`.
- Añadir una acción **Translate** en la vista lista de ambos modelos para
  abrir el asistente de traducción individual sobre la categoría seleccionada.
- Declarar `website_sale` como dependencia explícita del módulo.
- Si se seleccionan varias categorías, abrir automáticamente el asistente
  `translation_bulk` con todos los registros seleccionados.
- Para `product.category` y `product.public.category`, limitar los campos
  traducibles del asistente exclusivamente a `name`.
- Activar `translate=True` en `product.category.name`, que no es traducible
  por defecto en Odoo, conservando el campo como obligatorio e indexado.
