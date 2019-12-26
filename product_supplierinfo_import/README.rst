.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==========================
Product Suplierinfo Import
==========================

Uso
=====
 Desde la sección "Compras/Compra" seleccionar "Importar tarifa de compra",
en el asistente mostrado introducir el proveedor a actualizar y el fichero de
origen para la actualización, se realizará una validación previa y despues la
actualización con los datos facilitados en el fichero.

Notas
=====
 El campo "default_code" del fichero es requerido, también lo es el campo
"name" si se trata de un producto nuevo.

 El resto de campos y su descripción es la siguiente:
    -'price' : Precio de compra del producto
    -'list_price' : Precio de venta genérico del producto
    -'garage_price' : Precio de venta en la tarifa taller
    -'currency' : Moneda de la tarifa de compra
    -'min_qty' : Cantidad mínima para el reabastecimiento
