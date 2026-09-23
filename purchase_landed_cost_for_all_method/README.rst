===================================
Purchase landed cost for all method
===================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

El módulo matriz purchase_landed_cost solo aplica costes cuando el producto tiene el método de coste AVCO.
Con este módulo se añade la posibilidad de aplicar costes a los productos con los métodos de coste FIFO y estándar.

Para FIFO, puede que el precio de coste de la ficha del producto se actualice, mientras que para el método estándar nunca se actualiza.
El método FIFO solo actualizaría el precio de coste cuando el movimiento al que le afecta una imputación de costes
corresponde al siguiente movimiento que sea usado para la salida de mercacía.

**Tabla de contenidos**

.. contents::
   :local:

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_
