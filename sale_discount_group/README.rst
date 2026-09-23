===================
Sale Discount Group
===================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo permite definir descuentos comerciales por combinación de:

* Grupo de productos
* Grupo de clientes
* Rango de fechas

Con esa configuración, el descuento se aplica automáticamente en la línea de
pedido de venta cuando la combinación producto/cliente coincide con una regla
activa.

También añade una opción en las reglas de tarifa para decidir si se debe
aplicar o no el descuento por grupo.

**Tabla de contenidos**

.. contents::
   :local:


Configuración
~~~~~~~~~~~~~

1. Ve a **Ventas > Productos > Grupos de descuentos**.
2. Crea los grupos de:

   * **Product Group**: selecciona los productos que pertenecen al grupo.
   * **Partner Group**: selecciona los clientes que pertenecen al grupo.

3. Crea uno o varios registros en **Discount Group** indicando:

   * Nombre
   * Compañía
   * Fecha inicio y fecha fin (opcional fin)
   * Porcentaje de descuento
   * Grupo de productos
   * Grupo de clientes

4. En las reglas de tarifa (**Pricelist Rule**) revisa el campo
   **Apply Discount Group**:

   * Activado: permite aplicar el descuento del grupo.
   * Desactivado: bloquea la aplicación del descuento del grupo en esa regla.


Uso
~~~

1. Crea un presupuesto/pedido de venta para un cliente.
2. Añade una línea con un producto.
3. Si el cliente y el producto pertenecen a grupos con una regla válida en la
   fecha del pedido, se aplica automáticamente el porcentaje de descuento.
4. Si no hay coincidencia o la regla está fuera de vigencia, el descuento será
   0%.
5. Si la tarifa aplicable tiene **Apply Discount Group** desactivado, no se
   aplicará descuento por grupo.


Funcionamiento técnico
~~~~~~~~~~~~~~~~~~~~~~

El módulo añade:

* Modelo ``discount.group`` para reglas de descuento por combinación de grupos.
* Modelo ``discount.product.group`` para agrupar productos.
* Modelo ``discount.partner.group`` para agrupar clientes.
* Campo ``dto_group_id`` en ``product.template`` y ``res.partner``.
* Campo ``apply_discount_group`` en ``product.pricelist.item``.
* Lógica en ``sale.order.line`` para calcular el descuento en onchange de
  producto/cantidad/UdM.


Notas
~~~~~

* El descuento se evalúa por compañía.
* La regla debe estar vigente en la fecha del pedido.
* Si hay reglas de tarifa que no permiten descuento por grupo, tienen
  prioridad y el descuento queda en 0%.


Autor
~~~~~

* `Trey <https://www.trey.es>`__
