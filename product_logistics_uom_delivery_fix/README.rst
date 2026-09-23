==================================
Product logistics uom delivery fix
==================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Corrige el cálculo del peso en líneas de movimiento de albarán cuando
      el producto tiene una unidad de peso distinta a la del albarán.
    * Convierte el peso del producto desde su ``weight_uom_id`` a la unidad
      configurada en el albarán antes de sumar el total.
    * Evita casos en los que un producto definido en gramos se interpretaba
      como si estuviera en kilogramos en el módulo ``delivery``.

**Tabla de contenidos**

.. contents::
   :local:


Uso
~~~

* Instala el módulo junto con ``delivery`` y ``product_logistics_uom``.
* Define el peso del producto en la unidad adecuada, por ejemplo gramos.
* El peso de cada ``stock.move`` se recalculará en la unidad de peso del
  albarán antes de agregarse al total del picking.


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
