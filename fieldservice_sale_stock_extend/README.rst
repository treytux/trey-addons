.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Fieldservice sale stock extend
==============================

- Al modificar el campo "Almacén" de la orden de la orden de servicio de campo y guardar, se modifican las ubicaciones correspondientes de los albaranes:
    - Albarán de salida (si hay): se modifica la ubicación de origen por la ubicación de stock del almacén seleccionado.
    - Albaranes internos (si hay): se modifica la ubicación de destino por la ubicación de stock del almacén seleccionado.
    - Para poder rellenar el material necesario en la ubicación origen del albarán de salida desde el almacén definido en el pedido de venta, se crea un nuevo albarán interno o se añade un nuevo movimiento interno al albarán interno existente.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
