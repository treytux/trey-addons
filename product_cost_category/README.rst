.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Product Cost Category
=====================

Este módulo agrega una forma nueva de calcular el precio de venta
almacenándolo en un campo nuevo para su uso en las listas de precios. Usando
el precio de coste y unos rangos de aplicación se calcula este nuevo precio.


* Permite crear una categoría de coste con una fecha de vigencia para su
  aplicación.

* En la categoría de coste se define el rango desde-hasta basado en el
  standard_price para que se aplique dicha regla.

* La regla esta basada en una fórmula usando el standard_price.

* Agrega este campo nuevo "cost_category_price" tanto en los product.product
  como en los product.template.



**Table of contents**

.. contents::
   :local:

Configuración
=============

A nivel de ventas, tenemos un parámetro nuevo llamado Tipo de actualización
categoría de coste. Si lo establecemos en manual, solo se actualiza este precio
mediante el asistente de actualización.

Si lo establecemos en automático, cualquier proceso de odoo que actualiza el
standard_price actualizara el cost_category_price.

Uso
===

1. Se define una categoría de coste con una fecha de vigencia.
2. Se establece al menos un rango de coste y su fórmula.
3. Podemos usar el nuevo campo "cost_category_price" en las listas de precios.

