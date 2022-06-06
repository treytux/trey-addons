===========================
Stock picking check carrier
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Comprueba que los albaranes tengan asignado un transportista antes de ser validados.
    * Este comportamiento se controla según el tipo de operación del albarán.
    * Se añade un campo en el modelo stock.picking.type de tipo booleano.
    * Si el campo está activado, todos los albaranes de ese tipo de operación comprobarán que tienen transportista asignado antes de ser validados.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
