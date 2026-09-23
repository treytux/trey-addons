===========================
Product purchase last price
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo permite controlar el último precio de compra y su impacto en la
venta.

Funcionalidades principales:

* Añade el campo **Purchase last price** en producto y plantilla.
* Añade el campo **Margin on purchase last price (%)** como valor calculado.
* Al validar una recepción de compra, actualiza el último precio de compra del
  producto con el precio de la línea de compra.
* Guarda en cada línea de venta el último precio de compra del producto para
  poder analizar márgenes en contexto de venta.
* En la exportación de pivote de ventas, **% Margen** se calcula como
  ``(1-(purchase_last_price / operation_total))*100``.
* Recalcula el precio de compra en líneas de venta según los movimientos de
  stock, tomando la última entrada disponible hasta la fecha del movimiento.
* Cuando hay nuevas compras, actualiza las líneas de venta relacionadas dentro
  del intervalo entre recepciones del mismo producto.

Flujo de funcionamiento:

1. Se confirma y recibe una compra.
2. El movimiento de entrada en estado `done` actualiza el precio de compra del
   producto.
3. Las líneas de venta usan ese valor como referencia.
4. El margen sobre último precio de compra se calcula automáticamente.
5. Si ya se validó una salida y se modifica el precio de compra de la entrada,
   también se actualizan las ventas realizadas desde esa entrada hasta la
   siguiente, si existe.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
