.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

stock_mts_mtd_rule
==================

Este módulo añade una ruta de bajo existencias + bajo dropshipping.

Si elige la ruta de bajo existencias + bajo dropshipping en lugar de la de dropshipping, la creación de un pedido de compra de dropshipping dependerá del stock virtual. Hay 3 casos:

1. El stock virtual del producto es 0:
    => Actuará exactamente como la ruta de bajo dropshipping.

2. El stock virtual es igual a la cantidad pedida:
    => Actuará exactamente como una ruta de bajo existencias.

3. El stock virtual es mayor que 0 pero menor que la cantidad pedida:
    => Una parte de los productos se tomará de stock y otra creará un pedido de compra de dropshipping. Por lo tanto actuará como una regla bajo existencias y bajo dropshipping.

Ejemplo:
Disponemos de stock virtual de 1 ud de producto A.
Se realiza un pedido de venta para 3 uds de producto A.
Se crearán 2 abastecimientos:
    1. Uno con una ruta bajo existencias y una cantidad de 1 ud.
    2. Uno con una ruta dropshipping y una cantidad de 2 uds.

Después de la validación, se creará una pedido de compra de dropshipping con 2 unidades del producto A.

Configuración
-------------

Debe seleccionar 'Usar reglas MTS+MTD' en el formulario de almacén.

Uso
---

Tiene que seleccionar la ruta "Make to stock + Make to dropshipping" en el formulario de producto.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
