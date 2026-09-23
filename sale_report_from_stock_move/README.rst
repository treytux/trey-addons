.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Sale report from stock move
===========================

Este módulo añade el informe **Ventas desde movimientos de existencias** en
Ventas > Informes. El informe relaciona los movimientos de existencias con sus
líneas de pedido de venta y permite analizar las ventas según el movimiento
logístico que las genera.

**Tabla de contenidos**

.. contents::
   :local:

Descripción
===========

El informe se basa en una vista SQL del modelo
``sale.report.from_stock_move``. Solo se incluyen movimientos que:

* están vinculados a una línea de pedido de venta;
* tienen un producto definido; y
* tienen como origen o destino una ubicación de tipo cliente.

Los movimientos de salida hacia un cliente se muestran con cantidades e
importes positivos. Los movimientos de devolución desde un cliente se muestran
con cantidades e importes negativos. Los movimientos entre ubicaciones
internas no generan importe de operación en el informe.

Funcionalidad
=============

El informe proporciona las siguientes vistas:

* **Gráfico:** evolución mensual del importe de operación.
* **Pivot:** análisis mensual del importe de operación, con posibilidad de
  aplicar agrupaciones y medidas adicionales.
* **Lista:** detalle de cada movimiento, incluyendo fecha, pedido, producto,
  cantidades, precios, ubicaciones, cliente, comercial, equipo de ventas,
  lista de precios y picking.
* **Búsqueda:** filtros por producto, categoría, fecha, pedido, cliente,
  dirección de entrega, ubicaciones, estado, provincia, código postal, ciudad,
  equipo de ventas y comercial.

Campos principales
==================

El informe incluye, entre otros, los siguientes datos:

* fecha y estado del movimiento;
* producto, categoría y unidad de medida;
* cantidad del movimiento;
* precio unitario y descuento de la línea de venta;
* importe del movimiento e importe de operación;
* pedido de venta y picking;
* ubicación de origen y ubicación de destino;
* cliente y dirección de entrega;
* provincia, código postal y ciudad del cliente de entrega;
* comercial del pedido, comercial del cliente y equipo de ventas;
* lista de precios y compañía.

Filtros y agrupaciones iniciales
================================

Al abrir el informe se aplican automáticamente estos filtros:

* movimientos con estado **Realizado**;
* movimientos de los últimos 365 días.

También es posible agrupar por compañía, provincia, ciudad, código postal,
cliente, dirección de entrega, fecha, categoría, producto, equipo de ventas y
comercial.

Uso
===

1. Instale el módulo con la aplicación Ventas y el inventario habilitados.
2. Acceda a **Ventas > Informes > Ventas desde movimientos de existencias**.
3. Seleccione la vista gráfica o pivot para analizar los datos, o cambie a la
   vista de lista para consultar el detalle de los movimientos.
4. Ajuste los filtros y agrupaciones según el análisis que necesite.

No requiere configuración adicional. Los datos se actualizan a partir de los
movimientos de existencias vinculados a pedidos de venta.

Dependencias
============

Este módulo depende de ``sale_stock``.

Consideraciones
===============

El informe es de solo lectura: sus datos se calculan a partir de una vista SQL
y no deben modificarse directamente. Los movimientos de inventario sin línea
de venta asociada no aparecen en el informe.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
