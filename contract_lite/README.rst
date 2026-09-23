Contract Lite
=============

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Lightweight recurring invoicing contracts for Odoo 16.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__


Descripción
~~~~~~~~~~~

Este módulo añade un sistema sencillo de contratos con facturación recurrente
por líneas, orientado a minimizar complejidad y fallos habituales en la
generación automática de facturas.

El contrato incluye un cliente y un nombre, y cada línea define el producto,
cantidad, unidad de medida, descuento y la recurrencia. La generación de
facturas puede ejecutarse manualmente desde el contrato o automáticamente
mediante un cron.

La descripción de las líneas y la referencia de la factura soportan marcadores
que se sustituyen al crear la factura.

Características
~~~~~~~~~~~~~~~

* Contratos simples (nombre y cliente) con estado borrador/activo.
* Líneas de contrato con:
  * Producto, cantidad, UoM, descuento y subtotal calculado.
  * Precio automático (desde la tarifa del cliente) o manual.
  * Recurrencia: día, semana, mes, trimestre, cuatrimestre, semestre y año.
  * Fechas: inicio, próxima factura, fin, fin de próximo periodo.
  * Cuenta analítica aplicada a la línea de factura.
* Generación de facturas:
  * Manual desde el formulario del contrato.
  * Recurrente mediante cron.
* Enlace entre contrato y facturas generadas (smart button).
* Marcadores (tokens) para:
  * Descripción de líneas de factura.
  * Referencia de la factura.

Uso
~~~

1. Vaya a **Contracts > Contracts** y cree un contrato.
2. Añada una o varias líneas con la recurrencia y fechas.
3. Pase el contrato a **Active**.
4. Use el botón **Create invoices** para generar facturas manualmente o espere
   a la ejecución del cron.

Marcadores disponibles
~~~~~~~~~~~~~~~~~~~~~~

Leyenda (para los marcadores dentro de descripción en líneas de factura):

* ``#START#``: Start date of the invoiced period
* ``#END#``: End date of the invoiced period
* ``#START_MONTH_INT#``: Start month as number (1, 2, 3)
* ``#START_MONTH_STR#``: Start month as text (January, February, March)
* ``#START_YEAR#``: Start year (2014, 2015, 2016)
* ``#END_MONTH_INT#``: End month as number (1, 2, 3)
* ``#END_MONTH_STR#``: End month as text (January, February, March)
* ``#END_YEAR#``: End year (2014, 2015, 2016)

Leyenda (para las marcas de la referencia de la factura):

* ``#MONTH_INT#``: Month as number (1, 2, 3)
* ``#MONTH_STR#``: Month as text (January, February, March)
* ``#YEAR#``: Year (2014, 2015, 2016)

Instalación
~~~~~~~~~~~

1. Copie el módulo en su carpeta de addons.
2. Actualice la lista de módulos en Odoo.
3. Instale el módulo desde el menú de aplicaciones.

Requisitos
~~~~~~~~~~

* Odoo 16.0 o superior.
* Contabilidad configurada para poder crear facturas.
* Los productos deben tener una cuenta de ingresos configurada (en el producto
  o en la categoría) para poder generar líneas de factura.

Créditos
~~~~~~~~

Desarrollado por Trey.

Licencia
~~~~~~~~

AGPL-3.0
