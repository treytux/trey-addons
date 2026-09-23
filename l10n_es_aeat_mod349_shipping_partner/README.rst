===================================
AEAT modelo 349 - Shipping partner
===================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Utiliza la dirección de envío de la factura (partner_shipping_id) para
los registros del modelo 349, en lugar de la dirección fiscal del partner.

Qué hace
========

* En los registros de operaciones (invoice records) y rectificaciones
  (refund records) del modelo 349, sustituye el partner de la línea de
  factura por la dirección de envío de la factura.
* Si la factura no tiene dirección de envío, usa el partner de la línea
  (comportamiento original).

Autor
=====

* `Trey <https://www.trey.es>`__