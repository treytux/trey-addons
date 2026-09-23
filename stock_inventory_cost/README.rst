.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

stock_inventory_cost
====================

Nuevo campo en ajuste de inventario donde se calcula el coste total de dicho inventario.

Para el cálculo se tienen en cuenta:

    - Ubicaciones:

        - Si la ubicación origen es "Pérdidas de inventario", entonces usaremos signo positivo.

        - Si la ubicación destino es "Pérdidas de inventario", entonces usaremos signo negativo.

    - Cantidad/unidades de medida:

        - Si la unidad de medida no coincide con la unidad de medida de compra, hay que hacer la conversión de la unidad de medida del movimiento  a la unidad de medida de compra.

    - Precio de coste del producto:

        - Se obtiene del campo "Precio de coste" de la ficha del producto.

Con todo lo anterior se aplica la fórmula para cada uno de los movimientos del inventario:

    coste total += signo * cantidad del movimiento (en unidad de compra) * coste del producto


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
