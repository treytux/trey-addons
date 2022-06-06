.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

purchase_order_invoice
======================

Amplía con nuevas funcionalidades el proceso de facturar los pedidos de compra.

Crea un asistente que antes de facturar solicita qué proceso quiere usar el usuario para facturar un pedido de compra:

- Facturar lo recibido y no facturado. Es el proceso estándar de Odoo, en el que crea una factura con los productos que se han recibido y aún no están facturados.
- Facturar todas las líneas no facturadas. Permite crear una factura con aquellas líneas que no se han facturado aún indiferentemente de si se ha recibido o no.
- Facturar todas las líneas. Creará una factura del pedido de compra completo, indistintamente de si se ha facturado o no, o si se ha recibido o no.

Además permite facturar varios pedidos de compra al mismo tiempo desde el listado de pedidos de compra tendrá disponible una acción para crear las facturas de los pedidos marcados.

Configuración
-------------

No necesita ninguna configuración.

Otras funcionalidades
---------------------

Ninguna

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
