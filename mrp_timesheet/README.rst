=============
MRP Timesheet
=============

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Imputación de partes de horas desde órdenes de fabricación.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__


Descripción
~~~~~~~~~~~

Este módulo permite imputar partes de horas directamente desde la vista de una
orden de fabricación.

La orden de fabricación se relaciona con el proyecto a través de la cuenta
analítica. Si existe un proyecto con partes de horas activados y la misma
cuenta analítica que la orden de fabricación, se propone como proyecto por
defecto en las líneas imputadas desde la pestaña de partes de horas.

Las imputaciones se registran en el modelo estándar de Odoo 16
``account.analytic.line`` y quedan vinculadas a la orden de fabricación.

Uso
~~~

1. Cree o abra un proyecto con partes de horas activados.
2. Configure una cuenta analítica en el proyecto.
3. Cree o abra una orden de fabricación con la misma cuenta analítica.
4. En la orden de fabricación, abra la pestaña de partes de horas.
5. Añada una línea indicando fecha, proyecto, descripción, horas y empleado.

Licencia
~~~~~~~~

AGPL-3.0
