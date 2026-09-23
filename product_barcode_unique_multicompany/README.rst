===================================
Product barcode unique multicompany
===================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo corrige la restricción del servidor para hacer que el código de barras del producto sea única por producto pero teniendo en cuenta que puede repetirse en compañías distintas.

Para ello se modifica la restricción sql original (barcode_uniq) para hacer que siempre se devuelva True y no la tenga en cuenta y se añade una función para comprobar correctamente la restricción.


**Tabla de contenidos**

.. contents::
   :local:

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_
