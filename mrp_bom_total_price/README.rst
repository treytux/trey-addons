===================
Mrp Bom Total Price
===================

Add bill of materials total price and show bill of materials price cost per product.

Recompute bom_prod_price_total and bom_lst_price_total


=========
ChangeLog
=========

8.0.1.0.0

- Recompute bom_prod_price_total and bom_lst_price_total as store field.
- Migration for recompute field from older version.
- mpr.bom.update_price_state for controlling is un manual update required recompute price.
- mpr.bom.is_manual_update for controlling is change list_price or standard_price for by user.
- mpr.bom.standard_formula and list_formula to calculate the cost and / or sale price os the product.
- A programmable task for checking prices.
- A programmable task for updating prices.
