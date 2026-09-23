.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Productos en biblioteca
=======================

Permite importar productos desde Excel a un catálogo temporal, revisarlos y
activarlos posteriormente como productos de Odoo.

Características
===============

* Importación de ficheros ``.xls`` y ``.xlsx``.
* Búsqueda por EAN y, si no existe, por ``product_code``.
* Agrupación de variantes mediante ``product_tmpl_code``.
* Procesamiento por bloques de 1.000 productos.
* Conservación del número de línea original en ``line_num``.

Uso
===

1. Acceda a **Product catalog > Import Excel**.
2. Seleccione el fichero y pulse **Import**.
3. Revise las líneas en **Product catalog > Catalog lines**.
4. Seleccione las líneas y pulse **Process lines** para activar los productos.

Formato del Excel
=================

Columnas principales:

* ``default_code``: referencia interna.
* ``product_code``: código del producto.
* ``ean``: código de barras.
* ``name``: nombre del producto.
* ``supplier_ref``: referencia del proveedor.
* ``product_tmpl_code``: código para agrupar variantes.
* ``attribute:<nombre>``: valores del atributo separados por comas.

Si ``product_code`` está vacío, se genera concatenando ``supplier_ref`` y
``default_code``.

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`__
