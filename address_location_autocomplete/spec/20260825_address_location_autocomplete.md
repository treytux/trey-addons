# Address location autocomplete

## Alcance

El módulo proporciona la búsqueda de `res.city.zip` y un widget frontend
configurable para integraciones web.

## Comportamiento

El widget recibe mediante `data-*` los nombres de los campos de ciudad,
código postal, país, provincia y `zip_id`. La validación final se mantiene en
el servidor y en las restricciones de `base_location`.
