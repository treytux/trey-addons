.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================
Product supplierinfo discount fix
=================================

Este módulo corrige un problema del módulo "product_supplierinfo_discount" al
calcular los descuentos de las líneas de proveedor de la ficha del producto.

Si la unidad de medida de compra no coincide con la unidad de medida de las
líneas de proveedor (product.supplierinfo) porque se haya realizado una
modificación posterior de la unidad, el cálculo de descuento se realiza con la
cantidad en la unidad de medida de venta en lugar de en la de compra, que es
la correcta.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
