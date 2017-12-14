.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================
Promotional Code Counter
========================

It adds a limit of uses per promotional code and a checkbox that allows only
one use of promotional code per partner.

Usage
=====

1. With an Admin user, check Website > Shopping Cart > Customize > Coupon Code

2. Create a pricelist with a promotional code.
If 'Unique per partner' is checked,
the coupon will apply only one time per partner, it doesn't matter quantity of available codes.
Else, the coupon will apply as many times as available codes, independently of partner.

3. In Shopping Cart, use the created promotional code before process checkout. If coupon is available and 'Unique per partner' is unchecked, it will discount one unit of their available codes when sale order is confirmed. When the same confirmed sale order is cancelled, available codes will increase one unit.
