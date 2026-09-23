=================================
Sale invoice policy all delivered
=================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Añade una nueva política de facturación de pedidos.
    * La nueva política solo permite facturar pedidos que ya hayan sido completamente entregados.
    * La política se mantiene mientras no se haya facturado ninguna línea.
    * En el caso de salida de productos con facturación y se realice devolución parcial: se tendrá en cuenta el funcionamiento por defecto de Odoo.
    * En el caso de salida de productos con facturación y se realice devolución completa: se tendrá en cuenta el funcionamiento por defecto de Odoo.
    * En el caso de que se desee realizar una entrega parcial habiendo creado un albarán para cancelar el resto de movimientos se permitirá facturar el pedido.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
