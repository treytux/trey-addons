======================================
Sales Team UTM Medium Fiscal Position
======================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Permite configurar mapeos de cuentas contables en posiciones fiscales según el
medio de marketing (UTM Medium) de forma granular por cada línea de mapeo.
Cuando se añade un producto a una línea de factura, si la factura tiene un medio
de marketing asociado y el mapeo de cuenta tiene configurado el mismo medio, se
aplica el mapeo de cuentas correspondiente de la posición fiscal.

**Tabla de contenidos**

.. contents::
   :local:

Funcionalidad
=============

Este módulo añade:

Campo en mapeo de cuentas
~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``medium_id``: Medio de marketing para el que aplica este mapeo de cuentas específico

Comportamiento
~~~~~~~~~~~~~~

* Cuando se añade un producto a una línea de factura:

  #. Se verifica si la factura tiene un medio de marketing
  #. Se verifica si la factura tiene una posición fiscal
  #. Se busca un mapeo de cuentas que coincida con:

     * El medio de marketing de la factura
     * La cuenta origen del producto

  #. Si se encuentra un mapeo con el medio correcto, se sustituye la cuenta por la cuenta destino
  #. Si no se encuentra, la cuenta permanece sin cambios (comportamiento estándar)

Uso
===

#. Ir a *Facturación > Configuración > Posiciones fiscales*.
#. Crear o editar una posición fiscal.
#. En la pestaña *Mapeo de cuentas*, añadir mapeos:

   * Cuenta en facturas: 700000
   * Cuenta a usar en su lugar: 700001
   * Marketing Medium: "Web ecommerce"

#. Crear una factura con:

   * Medio de marketing: "Web ecommerce"
   * Posición fiscal: la configurada anteriormente

#. Al añadir un producto con cuenta de ingreso 700000, se sustituirá por 700001
   solo si el medio coincide.

Ejemplo práctico
================

Configuración
~~~~~~~~~~~~~

* Medio UTM: "Web ecommerce"
* Posición fiscal: "FP Multi-medio"

  * Mapeo 1: 700000 → 700001 (Medium: Web ecommerce)
  * Mapeo 2: 700000 → 700002 (Medium: Tienda física)

* Producto: "Servicio X"

  * Cuenta de ingreso: 700000

Resultado
~~~~~~~~~

* Factura con medio "Web ecommerce" → la cuenta 700000 se cambia a 700001
* Factura con medio "Tienda física" → la cuenta 700000 se cambia a 700002
* Factura sin medio → la cuenta 700000 permanece sin cambios
* Factura con medio diferente → la cuenta 700000 permanece sin cambios

Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`__:
