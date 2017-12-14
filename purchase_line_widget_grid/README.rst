.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================================
Handle easily multiple variants on Purchase Orders
=================================================

This module allows to add/modify of all the variants of a product in a direct
screen without the need of handling them one by one

Configuration
=============

#. Configure your user to have any permission from "purchase" group.
#. Create a product with 2 attributes and several values.

Usage
=====

#. Go to Purchase > Purchase > Quotations
#. Create a new quotation or edit an existing one.
#. Press "Add variants" button located in the upper right corner of the
   "Order Lines" tab.
#. A new screen will appear allowing you to select the products that have
   variants.
#. Once you select the product, a 2D matrix will appear with the first
   attribute values as columns and the second one as rows.
#. If there are already order lines for the product variants, the current
   quantity will be pre-filled in the matrix.
#. Change the quantities for the variant you want and click on "Transfer to
   order"
#. Order lines for the variants will be created/removed to comply with the
   input you have done.

As extra feature for saving steps, there's also a button on each existing line
that corresponds to a variant that opens the dialog directly with the product
selected.
