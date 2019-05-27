.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================================
Account invoice price recalculation
===================================

This module adds a button on account invoices (below invoice lines) that
recalculate the prices of the invoice lines that contain a product in them.

It is launched manually as a button to get the user decide if he/she wants to
recalculate prices when pricelist is changed or after duplicating an invoice
order to actualize or not invoice prices.

Usage
=====
Inside a account invoice, you can click on "Recalculate prices" button to
launch a recalculation of all the prices of the lines, losing previous custom
prices.

Note
=====
This module is based in "sale_order_price_recalculation" module to
"https://github.com/OCA/sale-workflow.git" branch but for account invoice
lines.
