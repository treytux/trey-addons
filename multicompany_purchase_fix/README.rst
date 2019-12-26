.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================
Multicompany purchase fix
=========================

This module fixs errors in multi-company purchase order environments:

ERROR:
------

When the "Run mrp scheduled" planner is automatically executed and will create
a purchase quotation, it searches for a supplierinfo record for the
corresponding product template and supplier but does not take the company into
account, so if it finds more than one, when accessing the min_qty field it
gives the following error:
    Expected singleton: product.supplierinfo(id_x, ix_y)

SOLUTION:
--------
    
Add the "company_id" key with the value of the current company to the context
in the "make_po" function and correct the searches of the
"product.supplierinfo" object in the "_calc_new_qty_price" function so that
the company is taken into account in the search.
