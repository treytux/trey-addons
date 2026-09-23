===========
Sale Return
===========

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Este módulo permite hacer pedidos de venta para devoluciones y cambios.
    * IMPORTANTE: antes de utilizar el módulo hay que asegurarse de que el campo "Tipo de devolución" de los tipos de operaciones de entrada deben estar rellenos (este campo sólo se queda vacío si se crea manualmente un nuevo tipo de operación).
    * IMPORTANTE: Este módulo es incompatible con sale_invoice_policy_return, si se utiliza, habrá que redefinir el método _compute_qty_to_invoice() en el módulo de personalización del cliente.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
