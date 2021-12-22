.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

sale_stock_product_pack
=======================

Nuevo módulo para gestionar correctamente los productos de tipo pack "Detallado" ("Detallado por componente", "Totalizado en el producto principal" e "Ignorado"):

- En el albarán generado desde el pedido de venta se eliminan las líneas de los productos de tipo pack, dejando sus componentes.

- Se modifica el cálculo de los campos "Cantidad enviada" y "Cantidad facturada" de las líneas de pedido de venta para que se calculen en base a los componentes entregados y facturados.

- Si se envía más cantidad de la que hay definida en el movimiento, al crearse la factura se creará otra línea con la cantidad excedida y el precio que corresponda.


IMPORTANTE
----------

Actualmente el tipo de pack "No detallado" no está contemplado ya que, al no añadir al pedido de venta las líneas de los componentes del pack, no se puede usar el flujo por defecto que hace que se lancen de forma automática las reglas de stock y se creen los abastecimientos.

NOTA: si algún cliente lo pide es más fácil que use alguno de los subtipos detallados y se pueden modificar sus informes personalizados para que no se muestren en los informes los productos que sean componentes.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
