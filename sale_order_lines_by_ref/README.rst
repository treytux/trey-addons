.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Sale order lines by ref
=======================

Asistente para añadir líneas de pedidos de venta usando las referencias internas,
con el objetivo de facilitar la entrada de pedidos de forma más mecánica.

En el pedido de venta aparece un botón para introducir líneas, en las líneas
puede introducir la información de [referencia],[cantidad],[precio unitario] como
en este ejemplo:

REF0001/5/10.10
REF0002/8
REF0003

Esta información crea 3 líneas para los productos REF0001, REF0002 y REF0003

Puede cambiar el carácter de pegamento utilizando el parámetro del sistema:
'sale_order_lines_by_ref.glue'

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
