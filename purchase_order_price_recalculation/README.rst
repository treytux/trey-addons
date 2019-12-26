.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
Purchase order price recalculation
==================================

This module adds a button on purchase orders (below order lines) that
recalculate the prices of the order lines that contain a product in them.

It is launched manually as a button to get the user decide if he/she wants to
recalculate prices when pricelist is changed or after duplicating a purchase
order to actualize or not purchase prices.

Usage
=====
Inside a purchase order, you can click on "Recalculate prices" button to
launch a recalculation of all the prices of the lines, losing previous custom
prices.

Note
=====
This module is based in "sale_order_price_recalculation" module to
"https://github.com/OCA/sale-workflow.git" branch but for purchase order lines.
