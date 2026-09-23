Contract Lite Supplier
======================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Contratos recurrentes de proveedor para Odoo 16.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__


Descripción
~~~~~~~~~~~

Este módulo permite gestionar contratos ligeros de proveedor y generar
facturas de proveedor en borrador de forma recurrente, tomando como base
las líneas del contrato.

La funcionalidad está disponible en:

*Contabilidad > Proveedores > Contratos*


Funcionalidades principales
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Contratos de proveedor con estado (Borrador, Activo, Cerrado).
* Líneas recurrentes por contrato con:
  - Producto, cantidad, UoM, descuento.
  - Precio automático o manual.
  - Regla de recurrencia (días, semanas, meses, trimestres, etc.).
  - Fechas de inicio, próxima factura y fin.
* Generación manual de facturas de proveedor desde el contrato.
* Generación automática diaria mediante tarea programada.
* Facturas de proveedor en estado borrador (`in_invoice`).
* Trazabilidad de contrato y línea de contrato en `account.move` y
  `account.move.line`.


Configuración
~~~~~~~~~~~~~

Antes de usar el módulo, revisar:

* Diario de compras disponible en la compañía.
* Proveedores con datos contables básicos configurados.
* Productos con cuenta de gasto correctamente definida.


Uso
~~~

1. Ir a *Contabilidad > Proveedores > Contratos*.
2. Crear un contrato y seleccionar proveedor.
3. Añadir una o varias líneas recurrentes.
4. Activar el contrato.
5. Generar facturas:
   - Manualmente con *Create vendor bills*.
   - Automáticamente con el cron diario.

Las líneas elegibles se agrupan por:

* Compañía
* Proveedor
* Contrato
* Fecha de próxima factura

Tras crear la factura, se actualiza la siguiente fecha de recurrencia en
cada línea procesada.


Notas
~~~~~

* El módulo no añade portal para esta funcionalidad.
* El menú de entrada es único en Proveedores (sin menú separado de líneas).
* Si un producto no tiene cuenta de gasto configurada, se mostrará un error
  de validación al generar la factura.

Créditos
~~~~~~~~

Desarrollado por Trey.


Licencia
~~~~~~~~

AGPL-3.0
