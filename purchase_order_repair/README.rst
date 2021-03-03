.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Purchase order repair
=====================

This module creates two new types of operation: shipment repairs and reception
repairs. The reception repair type is marked by default the option 'Create
automatic return picking' to automatically create the return picking.

When a purchase order is created to ship products to be repaired to a supplier,
in the field 'Deliver to' you must select the new type of operation 'Reception
of repairs'. When the purchase order is confirmed, two stock pickings will be
generated:

    - One output (shipment) in 'Ready to transfer' state to send the products
    to repair to the supplier. The invoice control is fixed to 'Not
    Applicable' because the supplier is not going to invoice anything.

    - One entry (reception) in 'Waiting another operation' state so that, once
    the shipping stock picking has been transferred to the supplier, it
    automatically goes to the 'Ready to transfer' state and is received when
    the supplier has repaired it.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
