=====================================
Stock picking optional package number
=====================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Muestra u oculta el campo 'Número de bultos' del asistente para confirmar albaranes según lo definido en el campo 'Mostrar el número de bultos en el asistente' del tipo de operación.
    * Este comportamiento se controla según el tipo de operación del albarán.
    * Se añade un campo en el modelo stock.picking.type de tipo booleano.
    * Si el campo no está activado, en los albaranes de ese tipo de operación no será necesario indicar el número de bultos en el asistente.
    * El asistente puede confirmar varios albaranes con diferentes tipos de operación.
    * En el caso de que todos los tipos de operaciones de los albaranes tengan la misma configuración se toma el comportamiento único.
    * Si hay albaranes con tipos de operaciones con diferentes configuraciones se toma la configuración por defecto que es mostrar el campo 'Número de bultos' en el asistente.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
