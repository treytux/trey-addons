======================
Website sale reference
======================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Añade un campo 'Referencia' en el carrito de la tienda web.
    * La referencia se guarda en el campo client_order_ref del pedido de venta
      mediante una llamada JSON al perder el foco del campo.
    * La referencia se muestra (solo lectura) en las páginas de pago y de
      confirmación.

**Tabla de contenidos**

.. contents::
   :local:


Configuración
~~~~~~~~~~~~~

No requiere configuración. Basta con instalar el módulo.


Uso
~~~

* En /shop/cart el cliente escribe una referencia de pedido opcional.
* El valor se persiste automáticamente en el pedido de venta
  (campo "Referencia del cliente").
* La referencia aparece en /shop/payment y en /shop/confirmation, y en el
  pedido de venta del backend.


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
