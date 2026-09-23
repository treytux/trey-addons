==============================
Product list price from margin
==============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo calcula automáticamente el precio de venta de los productos a
partir del coste y del margen comercial deseado.

Funcionalidades principales:

* Añade el campo **Margin (%)** a los productos y sus variantes.
* Calcula el precio de venta a partir del coste y del margen.
* Recalcula el margen cuando se modifica el precio de venta.
* Permite establecer márgenes y precios independientes para cada variante.
* Añade **Variant price list** como base de cálculo para las reglas de tarifas.
* Limita el margen máximo al 99,99 %.

La fórmula utilizada es::

    Precio de venta = Coste / (1 - Margen / 100)

Por ejemplo, con un coste de 100 EUR y un margen del 25 %, el precio de venta
calculado es 133,33 EUR.

Configuración
=============

El módulo depende de los módulos ``product`` y ``purchase_discount``.

Para utilizar la base **Variant price list** en una tarifa:

1. Activa las listas de precios desde **Ventas > Configuración > Ajustes**.
2. Selecciona las reglas de precio avanzadas.
3. Abre una tarifa desde **Ventas > Productos > Tarifas**.
4. Crea una regla con cálculo por **Fórmula**.
5. Selecciona **Variant price list** como base de cálculo.

Uso
===

1. Abre un producto desde **Ventas > Productos > Productos**.
2. Define su coste.
3. Abre la variante del producto.
4. Introduce el margen en **Margin (%)**.
5. Guarda el producto y comprueba el precio de venta calculado.

En productos con varias variantes, el margen y el precio se gestionan en cada
variante. La base **Variant price list** utiliza el precio concreto de la
variante al calcular una tarifa.

Autor
=====

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

Licencia
========

Este módulo está licenciado bajo AGPL-3.
