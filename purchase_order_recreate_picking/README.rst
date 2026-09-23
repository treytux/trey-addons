.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Purchase Order Recreate Picking
===============================

Descripción
===========

Este módulo permite recrear el albarán pendiente de una orden de compra
confirmada cuando ha sido eliminado o necesita generarse de nuevo.

Funcionamiento
==============

Desde la orden de compra, en estado ``Pedido de compra``, se puede utilizar el
botón ``Recreate picking``. El nuevo albarán se genera únicamente con las
cantidades pendientes de recibir.

El botón no está disponible si la orden tiene un albarán pendiente. Tampoco se
puede recrear el albarán cuando la cantidad devuelta supera la cantidad
recibida.

Configuración
=============

No requiere configuración adicional.

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
