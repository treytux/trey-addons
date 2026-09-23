=========================
Website Sale Observations
=========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Añade un campo 'Observaciones' en el carrito de la tienda web, justo
      debajo del campo 'Número de referencia' de ``website_sale_reference``.
    * Las observaciones se guardan en el campo ``web_order_observations`` del
      pedido de venta mediante una llamada JSON al perder el foco del campo.
    * Las observaciones se muestran (solo lectura) en las páginas de pago y de
      confirmación, y en el formulario del pedido de venta del backend.

**Tabla de contenidos**

.. contents::
   :local:

Uso
~~~

* En /shop/cart el cliente escribe unas observaciones opcionales.
* El valor se persiste automáticamente en el pedido de venta
  (campo "Web order observations").
* Las observaciones aparecen en /shop/payment y en /shop/confirmation, y en el
  pedido de venta del backend.


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
