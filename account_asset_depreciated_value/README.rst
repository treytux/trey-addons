===============================
Account asset depreciated value
===============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Modificación del cálculo de las líneas de amortización.
    * Se añaden dos nuevos campos en la cabecera de los activos.
    * Los nuevos campos son: "Valor pendiente de amortización" y "Fecha pendiente de amortización".
    * Al calcular las líneas solo se añaden aquellas con fecha igual o posterior a la indicada en el nuevo campo.
    * La primera línea se iniciará con el valor pendiente de amortizar.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
