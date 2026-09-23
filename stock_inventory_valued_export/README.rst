.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock inventory valued export
=============================

Este módulo añade un nuevo asistente "Exportar valoración de inventario" en el menú "Inventario/Informes" que genera un fichero excel con la valoración de inventario para la fecha actual o para una fecha específica.

El fichero generado muestra las siguientes columnas:
    - Producto: nombre del producto.
    - Categoría de producto: nombre de la categoría a la que pertenece el producto.
    - Ubicación: nombre de la ubicación.
    - Cantidad: cantidad a mano que hay en la ubicación.
    - Precio de coste: precio de coste de la ficha del producto.
    - Subtotal: se calcula multiplicando la cantidad por el precio de coste.

Además, al final muestra el total, que es el sumatorio de la columna "Subtotal".

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
