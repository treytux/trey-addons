.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Spreadsheet Environment Functions
=================================

Este módulo añade funciones personalizadas a las hojas de cálculo de Odoo
para consultar datos de cualquier modelo usando dominios.

Funciones disponibles
=====================

ODOO.ENV.SUM
------------

Obtiene la suma de un campo para los registros que coinciden con un dominio.

**Sintaxis:** ``=ODOO.ENV.SUM(modelo, campo, dominio)``

**Ejemplo:**

.. code-block::

    =ODOO.ENV.SUM("sale.order", "amount_total", "[('state','=','sale')]")

ODOO.ENV.AVG
------------

Obtiene el promedio de un campo para los registros que coinciden con un dominio.

**Sintaxis:** ``=ODOO.ENV.AVG(modelo, campo, dominio)``

**Ejemplo:**

.. code-block::

    =ODOO.ENV.AVG("sale.order", "amount_total", "[('state','=','sale')]")

ODOO.ENV.COUNT
--------------

Cuenta los registros que coinciden con un dominio.

**Sintaxis:** ``=ODOO.ENV.COUNT(modelo, dominio)``

**Ejemplo:**

.. code-block::

    =ODOO.ENV.COUNT("sale.order", "[('state','=','sale')]")

ODOO.ENV.MIN
------------

Obtiene el valor mínimo de un campo para los registros que coinciden con un dominio.

**Sintaxis:** ``=ODOO.ENV.MIN(modelo, campo, dominio)``

**Ejemplo:**

.. code-block::

    =ODOO.ENV.MIN("sale.order", "amount_total", "[('state','=','sale')]")

ODOO.ENV.MAX
------------

Obtiene el valor máximo de un campo para los registros que coinciden con un dominio.

**Sintaxis:** ``=ODOO.ENV.MAX(modelo, campo, dominio)``

**Ejemplo:**

.. code-block::

    =ODOO.ENV.MAX("sale.order", "amount_total", "[('state','=','sale')]")

Parámetros
==========

- **modelo**: Nombre técnico del modelo (ej: 'sale.order', 'res.partner')
- **campo**: Nombre del campo a agregar (debe ser numérico: integer, float o monetary)
- **dominio**: Dominio de Odoo como string (ej: "[('state','=','sale')]")

Notas
=====

- El campo debe ser de tipo numérico (integer, float o monetary)
- El dominio se evalúa en el servidor
- Las funciones usan sudo() para acceder a los datos


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
