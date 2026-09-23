.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock inventory valued export extend
=============================

Este módulo amplía la funcionalidad del módulo de stock_inventory_valued_export, añadiendo información más detallada.

El fichero generado muestra las siguientes columnas:
    - Producto: nombre del producto.
    - Categoría de producto: nombre de la categoría a la que pertenece el producto.
    - Ubicación: nombre de la ubicación.
    - Cantidad: cantidad a mano que hay en la ubicación.
    - Precio de coste: precio de coste de la ficha del producto.
    - Subtotal: se calcula multiplicando la cantidad por el precio de coste.
    - Descripción: La descripción del producto.
    - Atributos: Los atributos del producto.
    - Pendiente de enviar: Pedidos de venta que aún no han salido de almacén.
    - Pendiente de recibir: Pedidos de compra que aún no han entrado
    - Cantidad neta: Cantidad disponible menos la cantidad que está pendiente de enviar.
    - Cantidad prevista: Cantidad disponible menos la cantidad que está pendiente de enviar, más la cantidad que está pendiente de recibir.
    - Última salida: La fecha del último movimiento de producto saliente.
    - Última entrada: La fecha del último movimiento de producto entrante.
    - Ventas mes actual: Las ventas del producto en el mes actual.
    - Ventas mes anterior: Las ventas del producto en el mes anterior.
    - Promedio 12 meses: El total de ventas en los últimos 12 meses entre 12.
    - Promedio 6 meses: El total de ventas en los últimos 6 meses entre 6.
    - Promedio 3 meses: El total de ventas en los últimos 3 meses entre 3.
    - Cantidad mínima: La cantidad mínima configurada para el producto.
    - Cantidad máxima: La cantidad máxima configurada para el producto.

Además, al final muestra el total, que es el sumatorio de la columna "Subtotal".

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
