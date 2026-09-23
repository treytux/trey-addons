===============================
Product Barcode Generator by ID
===============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo genera un código de barras para los productos a partir de campos secuencia que añade a categoría
y compañía.

El código se compone de los prefijos de ambas secuencias, categoría y luego compañía, seguido del ID del producto
con un relleno de hasta doce '0's.

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

El módulo añade un botón en el encabezado de la plantilla de producto:

1. Añade campos a compañía y categoría para gestionar las secuencias que se añadirán a los códigos de barras.
2. Al pulsarse el botón asigna el código de barras en base a los prefijos de compañía y categoría.

Créditos
========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

Licencia
========

Este módulo está licenciado bajo AGPL-3.
