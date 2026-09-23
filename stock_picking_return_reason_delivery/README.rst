====================================
Stock picking return reason delivery
====================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Añade a la razón de devolución un método de envío que es opcional.
    * La razón de devolucion sigue estando en el asistente para realizar una devolución de un albarán.
    * Cuando se realiza una devolución desde el albarán, si la razón de devolución tiene asignado un método de envío, éste se añade como línea al pedido de venta y se factura como corresponda:
        - Si se factura la devolución antes de haber facturado el envío inicial, se añadirá la línea de los portes a la factura emitida al cliente.
        - Si se factura la devolución después de haber facturado el envío inicial, se añadirá la línea de los portes como negativa en la factura rectificativa emitida al cliente.

** IMPORTANTE **
Odoo tiene la restricción de que, si creas un pedido de venta con productos con política de facturación "Cantidades pedidas", creas la factura, entregas la mercancía y luego devuelves la mercancía, si vas al pedido y generas la factura no crea factura rectificativa del producto devuelto.
Por lo tanto, sólo puede usarse método de envío en las razones de devolución si todos los productos del sistema tienen política de facturación "Cantidades entregadas".

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
