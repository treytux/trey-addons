.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Fieldservice add material
=========================

Añade un asistente para permitir que el operario, desde la orden de servicio,
pueda entregar el materíal ustilizado en la orden de servicio y añadir material
extra, que entrega al cliente y decidir si es o no facturable:

    - Si es facturable automáticamente se creará un nuevo pedido de venta cuyo
    almacén será el de la orden de servicio. El pedido se confirmará y su
    albarán de salida se transferirá, ya que, si lo lleva en el vehículo para
    entregarlo al cliente es porque tiene stock en su vehículo.
    Además se asociará este nuevo pedido a la orden de servicio mediante un
    mensaje en el muro.

    - Si no es facturable se creará un albarán de salida desde la ubicación de
    stock del vehículo hacia el cliente y se transferirá ya que, si lo lleva
    en el vehículo para entregarlo al cliente es porque tiene stock en su
    vehículo.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
