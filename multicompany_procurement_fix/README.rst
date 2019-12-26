.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============================
Multicompany procurement fix
============================

This module fixs errors in multi-company procurement order environments:

ERROR 1:
--------

When the "Run mrp scheduled" cron is executed automatically it is done
with the administrator user but, being in a multi-company environment, it will
be executed only for the company in which the administrator user is currently
identified, remaining the rest of procurementes not executed and with possible
security errors.

ERROR 2:
--------

If the module "account_auto_fy_sequence" is installed when executing the
cron "Run mrp scheduler" it this error occurrs:

    "The system tried to access to fiscal year sequence without specifying
the current fiscal year."

because in the context you do not pass the key "fiscalyear_id". This error
occurs in the background and is not displayed in the log or to the user but
is detected because the stock warehouse orderpoint orders are not executed.
If this module is not installed, there is no problem because it does not
affect normal operation.

SOLUTION:
--------
    
- Create a new cron "Run mrp scheduler (for company_id = 3)" for the new
company, leaving the original for the first.

- Pass in the parameters of the function called by the cron the company to
be able to pass the keys "fiscalyear_id" and "current_company_id" in the
context and to correct the original functionality.

NOTES/REQUIREMENTS
--------
    
- This module requires that you have created a fiscal year for each company in
the system.

- Modify the execution datetime of the crons so that they do not overlap.

- This module is currently configured for only two companies (see
multicompany_procurement_fix/data/data.xml file). If the database has more,
just create a new cron "Run mrp scheduler (for company_id = ID)" for each of
them, passing its ID in the arguments as follows: (True, ID). This process can
be done manually or by code by copying and pasting the original into another
module and making the necessary modifications to the ids.
