.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============
Product icon
============

Añade iconos a los productos, pensados sobre todo para el sitio web: muchos
productos necesitan iconos para detallar sus características, normativas,
composiciones, etc.

Aporta:

 - Modelo ``product.icon`` (nombre + imagen, con ``image.mixin``) y su maestro
   en Ventas > Configuración > Product icons.
 - Modelo ``product.template.icon`` y el One2many ``icon_ids`` en
   ``product.template``, con orden configurable por secuencia.
 - Pestaña de iconos en la ficha de producto (grupo "Icons" del bloque
   eCommerce).

No pinta nada en el frontend: de eso se encarga el módulo
``website_sale_product_icon``.

**Table of contents**

.. contents::
   :local:

Configuración
=============

En Ventas > Configuración > Product icons se dan de alta los iconos con su
imagen.

Uso
===

1. Se definen los iconos en el maestro de iconos de producto.
2. Se asignan dichos iconos a la plantilla de producto en la pestaña "Icons".
3. El orden de aparición se controla con la secuencia.

Créditos
========

Desarrollado por Trey.

Licencia
========

AGPL-3.0
