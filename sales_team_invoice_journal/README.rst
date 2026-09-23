===========================
Sales Team Invoice Journal
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Permite configurar un diario de facturación específico por equipo de ventas.
Cuando se factura un pedido de venta, la factura se genera automáticamente en el
diario configurado para el equipo de ventas del pedido.

**Tabla de contenidos**

.. contents::
   :local:

Funcionalidad
=============

Este módulo añade:

Campo en equipo de ventas
~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``invoice_journal_id``: Diario de facturas por defecto para pedidos del equipo

Comportamiento
~~~~~~~~~~~~~~

* Cuando se crea una factura desde un pedido de venta, si el equipo de ventas
  tiene configurado un diario de facturación, la factura se creará en ese diario
* Si el equipo no tiene diario configurado, se usa el diario por defecto de Odoo

Uso
===

#. Ir a *Ventas > Configuración > Equipos de ventas*.
#. Abrir o crear un equipo de ventas.
#. En el campo *Invoice Journal*, seleccionar el diario donde se crearán las facturas.
#. Crear un pedido de venta asociado a este equipo.
#. Al facturar el pedido, la factura se generará en el diario configurado.

Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`__:
