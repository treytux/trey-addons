.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Product pricelist import version
================================

Añade un asistente para importar versiones de tarifa sobre una tarifa de compras ya existente.
Este asistente se ubica en el menú Compras/Configuración/Importar tarifas de compra.

Hay que introducir:
   - Un tipo de tarifa (por defecto "Compras").
   - Una tarifa ya existente del tipo seleccionado.
   - Una opción que define en qué se basan los tipos de tarifa que se van a crear.
   - Un fichero xls cuya primera columna es la referencia interna del producto y la segunda el porcentaje de incremento para cada producto (si la columna "Incremento (%)" tiene un valor positivo se importará como un incremento. Si por el contrario es negativo, se importará como un descuento).

El asistente creará una nueva versión para la tarifa seleccionada indicando en el nombre la fecha actual y asignando como fechas de inicio y fin un año menos al actual para evitar que entre en vigor al ser importada (el usuario se encargará de revisar y actualizar las fechas de las versiones a posteriori). Dentro incluirá los siguientes elementos de tarifa:
   - Uno genérico para todos los productos basado en el precio de proveedor.
   - Uno por cada producto del fichero basado en el precio de proveedor y añadiendo el porcentaje de incremento en el precio.

Si existe ya alguna versión para dicha tarifa, se actualizará la fecha de inicio de la más actual para evitar que se solapen las fechas.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
