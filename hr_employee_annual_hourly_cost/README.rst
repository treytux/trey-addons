==============================
HR Employee Annual Hourly Cost
==============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Gestiona el coste hora del empleado por períodos de fechas.

**Tabla de contenidos**

.. contents::
   :local:


Descripción
~~~~~~~~~~~

Este módulo permite definir el coste hora de cada empleado por períodos
(``fecha inicio`` y ``fecha fin``), para reutilizar ese valor en cálculos de
costes históricos.

Configuración
~~~~~~~~~~~~~

1. Ir a **Empleados**.
2. Abrir la ficha del empleado.
3. En el bloque de **Hourly Cost**, añadir líneas en
   **Hourly cost periods**:
   - Fecha inicio del período.
   - Fecha fin del período (opcional).
   - Coste hora del período.

Reglas de negocio
~~~~~~~~~~~~~~~~~

- Si la fecha del parte cae dentro de un período, se usa ese coste hora.
- Si la fecha de fin está vacía, el período se considera abierto hasta hoy.
- Solo el período más reciente puede tener vacía la fecha de fin.
- No se permiten períodos solapados para un mismo empleado.
- Si no existe período aplicable, se usa el siguiente período futuro más
  cercano.
- Si no existe período futuro, se usa el ``hourly_cost`` actual del empleado.

Autor
~~~~~

* `Trey <https://www.trey.es>`__

Licencia
~~~~~~~~

AGPL-3.0
