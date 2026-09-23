
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Account fiscal position purchase
================================

Se añade un nuevo campo llamado "Posición fiscal compras" en la ficha del contacto.

Se modifica el funcionamiento de las funciones onchange que se ejecutan al modificar el campo Empresa de pedidos de compra y factura de modo que:

    - En el pedido de compra, se asigna la posición fiscal definida en el campo "Posición fiscal compras", si está rellena. Si está vacía no altera el funcionamiento nativo de Odoo, es decir, seguirá asignando el valor del campo "Posición fiscal".

    - En las factura de tipo proveedor o rectificativas de proveedor, se asigna la posición fiscal definida en el campo "Posición fiscal compras", si está rellena. Si está vacía no altera el funcionamiento nativo de Odoo, es decir, seguirá asignando el valor del campo "Posición fiscal".


Configuración
-------------

Rellenar el campo "Posición fiscal compras" en la ficha del contacto.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
