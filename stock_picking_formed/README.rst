====================
Stock picking formed
====================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Se añade el campo booleano 'formed' en los albaranes.
    * El usuario puede modificar el campo cuando el albarán se encuentre en el estado 'Preparado'.
    * Se realiza un seguimiento del valor del campo a través del hilo de conversaciones del albarán.
    * En el seguimiento del valor del campo debe indicarse el propio valor del campo, usuario que ha realizado la modificación y la hora en la que se ha realizado.
    * Desde el tipo de operación se puede configurar si conformar un albarán es obligatorio.
    * Se oculta el botón para marcar un albarán como conformado cuando el requerido no es obligatorio o no se encuentra en estado 'Preparado'.
    * Se oculta el campo 'Conformado' cuando el requerido no es obligatorio.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
