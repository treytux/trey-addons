====================================
Fieldservice sale order picking pack
====================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Se añade un nuevo campo en las plantillas de producto "Producto instalación"
que, si está marcado, mostrará el campo "Producto kit" que deberá ser de tipo
"Es un Pack?".

Si ese producto instalación además tiene marcada la opción "Servicio de
Seguimiento de Campo" y se añade a un pedido de venta, cuando se confirme,
el albarán de salida con los productos de las líneas del pedido de venta y la
orden de servicio de campo, creará un albarán de tipo interno con cada una de
los componentes del pack "Producto kit". Este albarán tendrá como origen la
ubicación de stock del almacén definido en el pedido de venta y como destino
la ubicación de stock del almacén definido por defecto en la orden de servicio
de campo.

Además se incluye un nuevo campo en las líneas de pedido de venta para
permitir vincular, si se quiere, los productos que no sean instalación con
algún producto que sí sea instalación. Esto se hará a través del asistente
"Relacionar con instalaciones".
Si no se vinculan, dichos productos no se vincularán a la orden de servicio de
ningún producto instalación, por lo que sus movimientos de stock sólo quedarán
relacionados con el pedido de venta mediante el albarán de salida.
Si se vinculan, además los movimientos de stock quedan relacionados con la
orden de servicio de la instalación correspondiente.


**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
