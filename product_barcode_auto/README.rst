====================
Product Barcode Auto
====================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo asigna automáticamente un código de barras (formato EAN13) único a los productos que no lo tengan configurado. El código generado utiliza el prefijo '84999', seguido del ID del producto y su correspondiente dígito de control.

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

El comportamiento del módulo es completamente automático y transparente para el usuario:

1. Al crear un nuevo producto, si el campo de código de barras está vacío, se generará uno automáticamente.
2. Al duplicar un producto existente, la copia recibirá un nuevo código de barras único, evitando conflictos.
3. Si se elimina manualmente el código de barras de un producto existente, el sistema le asignará uno nuevo de inmediato.
4. El sistema descarta códigos de barras duplicados si se intentan forzar durante la creación desde código o importación.

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
