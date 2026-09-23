.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Sale report from stock move
===========================

Añade el informe "Ventas desde movimientos de existencias" en el menú Ventas/Informes.

Cuando están seleccionadas las medidas ``Price Unit`` y ``Price Operation``,
se añade una nueva columna llamada ``% Margen`` calculado como
``1 - (price_unit / operation_total) * 100``.
Si falta una de esas medidas, la exportación se descarga igualmente, pero
sin la columna ``% Margen``.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
