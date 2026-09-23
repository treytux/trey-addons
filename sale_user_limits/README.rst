============================
Límites de usuario en ventas
============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Controla el importe de ventas y el descuento que cada usuario puede aplicar a
los pedidos de venta. Los pedidos que superan cualquiera de estos límites pasan
al estado de aprobación pendiente hasta que un usuario con límites suficientes
los aprueba.


**Tabla de contenidos**

.. contents::
   :local:


Configuración
=============

#. Ir a *Ajustes > Usuarios y compañías > Usuarios*.
#. Abrir el usuario que creará los pedidos de venta.
#. En la sección *Límites*, configurar:

   * *Importe máximo sin impuestos para operación libre*: importe máximo del
     pedido sin impuestos que el usuario puede confirmar sin aprobación.
   * *Descuento máximo por línea de pedido de venta (%)*: porcentaje máximo de
     descuento que el usuario puede aplicar a una línea sin aprobación.

Uso
===

Cuando un usuario confirma, envía, imprime o previsualiza un presupuesto que
supera uno de sus límites configurados, el pedido pasa a *Pendiente de
aprobación* y se muestra el motivo de la excepción en el pedido. El pedido se
puede cancelar o aprobar desde el formulario del pedido.

Después de la aprobación, el pedido vuelve al estado de presupuesto y se puede
confirmar normalmente. La lista de pedidos también incluye un filtro
*Pendiente de aprobación*.

Notas
=====

* El límite de importe se comprueba sobre el total del pedido sin impuestos.
* El límite de descuento se comprueba de forma independiente en cada línea del
  pedido de venta.
* La aprobación registra en el pedido el importe y los descuentos aprobados.
* El módulo depende de ``sale_management``.

Créditos
========

Autor
~~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__
