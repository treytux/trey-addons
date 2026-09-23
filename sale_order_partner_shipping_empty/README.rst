Sale order partner shipping empty
=================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Previene la asignación automática de direcciones de envío por defecto en los pedidos de venta.

**Tabla de contenidos**

.. contents::
   :local:

Descripción
===========

Este módulo impide que se asignen automáticamente direcciones de envío por defecto en los pedidos de venta.
Está diseñado para usuarios que pertenezcan al grupo *"Pedido de venta: No establecer dirección de entrega por defecto"*,
permitiéndoles controlar manualmente la dirección de envío en cada pedido.

Uso
===

#. Asigna a los usuarios el grupo "Pedido de venta: No establecer dirección de entrega por defecto".
#. Al crear nuevos pedidos de venta, no se establecerá una dirección de envío por defecto.
#. Los usuarios podrán seleccionar manualmente la dirección de envío deseada.

Dependencias
============

Este módulo depende de los siguientes módulos:

* ``sale``

Créditos
========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

Licencia
========

AGPL-3

``sale_order_partner_shipping_empty`` está licenciado bajo la Licencia GNU Affero General Public License v3.0.
