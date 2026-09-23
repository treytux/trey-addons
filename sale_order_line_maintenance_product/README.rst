.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Sale Order Line Maintenance Product
===================================

Este módulo permite añadir de forma automática una línea de pedido de venta de un producto de mantenimiento cuando se crea un pedido de venta.

Esta línea de mantenimiento se añadirá siempre que la compañía tenga configurado un producto de mantenimiento.

Se modifica el informe de pedido de venta para que no se muestren las líneas con precio 0, de esta forma no se mostrará la línea del mantenimiento si han desmarcado todas las líneas o no hay ninguna línea que afecte al mantenimiento.


Configuración
-------------

- En Compañía y Ajustes/Opciones Generales/Ventas:
   - Producto de mantenimento: el precio mínimo que se usará para dicho mantenimiento es el precio de venta definido en este producto (list_price).

- Plantillas de producto afectadas por el mantenimiento:
   - Porcentaje que va a incrementar al precio del producto de mantenimiento (por defecto 0 para que no le afecte).

Funcionamiento
--------------

- Para calcular el importe de la línea del producto de mantenimiento que se añadirá de forma automática, se suman los porcentajes de los precios unitarios de los productos que afectan al mantenimiento (los que tengan el check "¿No incrementa el precio de mantenimiento?" desmarcado en la línea) de la siguiente forma:
   - Si es mayor que el precio mínimo establecido, se asigna el precio calculado.
   - Si es menor que el precio mínimo establecido, se asigna el precio unitario configurado en el producto de mantenimiento.
El recálculo se hace cuando se cree o se modifique cualquier línea del pedido, ya que afectan tanto el check, como el precio, la cantidad y el descuento.

- La descripción de la línea de mantenimiento se calcula indicando la referencia interna y el nombre del producto de mantenimiento junto al listado de cantidades y referencias internas de los productos a los que le afecta dicho mantenimiento y no puede ser modificada manualmente por el usuario.

- La línea de mantenimiento no puede ser modificada manualmente por el usuario.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
