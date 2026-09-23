======================
Product Pricelist Base
======================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Módulo base para extender el cálculo de tarifas de Odoo. Centraliza la
selección de reglas y el cálculo de precios para que otros módulos puedan
añadir condiciones adicionales a las tarifas.

**Tabla de contenidos**

.. contents::
   :local:

Características
~~~~~~~~~~~~~~~

* Selecciona reglas aplicables por producto, plantilla, variante o categoría.
* Tiene en cuenta las categorías padre del producto al evaluar una regla.
* Filtra las reglas por cantidad mínima y fechas de inicio y finalización.
* Permite calcular el precio a partir del precio de venta, el coste o otra
  tarifa.
* Aplica precios fijos, descuentos porcentuales y fórmulas con redondeo,
  recargos y márgenes mínimos y máximos.
* Convierte cantidades y precios según la unidad de medida y la moneda de la
  tarifa.

Uso
~~~

Este módulo no añade menús ni pantallas de configuración. Se instala como
dependencia de módulos que necesiten modificar el proceso de cálculo de las
tarifas.

Las tarifas se gestionan desde la funcionalidad estándar de Odoo. Al calcular
un precio, el módulo busca la primera regla válida para el producto, la
cantidad, la fecha y la tarifa seleccionada, y devuelve el precio resultante
junto con la regla aplicada.

También permite proporcionar un precio mediante el contexto de Odoo usando la
clave ``force_price``. En ese caso, dicho precio se utiliza directamente.

Autor
~~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__
