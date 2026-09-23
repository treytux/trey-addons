========================
Product Supercode Search
========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo añade un campo ``supercode`` calculado y almacenado en las
plantillas de producto (``product.template``) y en las variantes
(``product.product``), que agrega en una única cadena de texto los datos
útiles para la búsqueda: nombre, referencias internas de todas las
variantes, códigos de barras, los códigos de los proveedores
(``product.supplierinfo``) y los códigos de los clientes
(``product.customerinfo``).

La búsqueda principal de productos y variantes pasa a realizarse sobre este
campo ``supercode``.

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

1. El campo ``supercode`` se recalcula automáticamente al cambiar el nombre,
   las referencias internas de las variantes, los códigos de barras o los
   datos de los proveedores y clientes.
2. En la vista de plantilla de producto, la caja de búsqueda principal busca
   por ``supercode``.
3. En la vista de variantes de producto, la caja de búsqueda principal busca
   por ``supercode``, que además incluye el ``supercode`` de su plantilla.

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
