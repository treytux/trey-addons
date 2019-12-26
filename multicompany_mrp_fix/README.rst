.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================
Multicompany mrp fix
====================

This module fixs errors in multi-company manufacturing environments:

ERROR:
    When confirming a sales order with a manufactured product, the "_bom_find"
    function does not find the "company_id" key in the context and mistakenly
    selects a list of materials from another company.
    The same happens when the "run_schudeled" scheduler is executed.

SOLUTION:
    Inherit the "_action_explode" and "_bom_find" functions to add in the
    context the "company_id" key with the company value of the current user to
    select the list of materials from those of the current company.
    In the case of the cron call, the value stored in context
    ['current_company_id'] is used.
