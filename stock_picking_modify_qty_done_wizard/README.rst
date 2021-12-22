.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

stock_picking_modify_qty_done_wizard
====================================

Asistente para facilitar la entrada de información en la recepción y salida de material, sin necesidad de asignar lotes ni ubicaciones, ni tener que abrir línea a línea un pop-up para introducir la cantidad movida en el campo "Hecho".


Uso
----
El botón "Modificar cantidades realizadas" que lanza el asistente se muestra encima de los movimientos de stock en todos los albaranes que no estén en los estados "Borrador", "Cancelado" o "Realizado".

Se añaden 3 botones dentro del asistente para facilitar aún más la asignación de valores:
    - Al pulsar el botón "Todo a 0" la columna 'Hecho' de todas las líneas se establecerá a cero.
    - Al pulsar el botón "Todo a reservado" la columna 'Hecho' de todas las líneas se establecerá al valor que haya en la columna 'Reservado'.
    - Al pulsar el botón "Todo a necesaria" la columna 'Hecho' de todas las líneas se establecerá al valor que haya en la columna 'Demanda inicial'.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
