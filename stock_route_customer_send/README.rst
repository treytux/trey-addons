.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock route customer send
=========================

Este módulo crea una ruta de inventario llamada "Envío a cliente".
Cuando esta ruta se usa en una línea de pedido de venta y se confirma el pedido, entonces:

    * Se crea un nuevo pedido de compra al proveedor que corresponda vinculado al pedido de venta.
    * El nuevo pedido de compra tiene como dirección de entrega la del cliente al que se le ha hecho la venta.
    Si el pedido de compra es de tipo "Envío a cliente", se marcará como tal y se mostrará la dirección de envío y la referencia del cliente.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
