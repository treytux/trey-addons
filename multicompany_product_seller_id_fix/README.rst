.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
Multicompany product seller id fix
==================================

This module overwrites the 'seller_id' field of the product template to prevent it from storing the value of the first supplierinfo it finds without taking into account the company in which the identified user is.
With this modification the field is converted to compute and filtered by company to avoid the error of access to partners of another company.

Note
=====

This bug only affects when the database has more than one active company.
