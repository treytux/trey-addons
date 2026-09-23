==========================
Indian Localization Extend
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo amplía la localización india de Odoo para cubrir dos necesidades
habituales en la operativa diaria: informar datos logísticos en documentos
comerciales y automatizar la asignación de impuestos GST a partir del HS Code
del producto.

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

El módulo añade una pestaña ``Indian Transport`` en pedidos de venta, pedidos
de compra y facturas. En ella se pueden informar estos datos:

- Modo de transporte.
- Número de vehículo.
- Fecha de suministro.
- Lugar de suministro.

Cuando una factura se crea desde un pedido de venta o desde un pedido de
compra, estos valores se copian automáticamente a la factura para mantener la
trazabilidad del envío y del suministro.

Además, el módulo amplía el modelo de códigos HS para incluir el campo
``Rate``. Ese valor se utiliza para determinar automáticamente los impuestos
aplicables en:

- Líneas de pedido de venta.
- Líneas de pedido de compra.
- Líneas de factura de cliente y proveedor.

La lógica aplicada es la siguiente:

- Si la compañía o el partner no pertenecen a India, Odoo mantiene el
  comportamiento estándar.
- Si la compañía y el partner pertenecen a India y están en el mismo estado,
  se aplican impuestos CGST y SGST repartiendo el tipo indicado en el HS Code.
- Si la empresa y el partner pertenecen a India pero están en estados
  distintos, se aplica IGST con el tipo completo del HS Code.
- Si el HS Code tiene la tasa ``Nil``, no se aplican impuestos.

Configuración
=============

#. Ir a *Inventario > Configuración > Códigos HS* y completar el campo
   ``Rate`` en los códigos que se utilicen en India.
#. Asignar un HS Code a cada producto que deba calcular impuestos GST de forma
   automática.
#. Verificar que la compañía india tenga informado su estado.
#. Verificar que clientes y proveedores indios tengan informado su estado.

Notas
=====

- Si en una operación india no existe estado en la compañía o en el partner, el
  sistema mostrará un error y no permitirá continuar con el cálculo fiscal.
- Si un producto usado en una operación india no tiene HS Code, el sistema
  mostrará un error para evitar una asignación fiscal incorrecta.
- El módulo incorpora plantillas de impuestos adicionales para completar
  escenarios GST que no están cubiertos por defecto en la localización base.

Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`__
