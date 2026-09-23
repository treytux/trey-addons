=============
CRM Team Bank
=============

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

This module lets you configure the allowed bank accounts (res.partner.bank) per
Sales Team. Users can then select one of those accounts on quotations and
customer invoices, and the chosen account is printed on the corresponding PDF
report.

**Table of contents**

.. contents::
   :local:

Configuration
=============

1. Go to *CRM* / *Configuration* / *Sales Teams*.
2. Open the desired Sales Team.
3. In *Team bank accounts*, select the bank accounts that belong to the
   company partner and should be available for documents created with this team.

Usage
=====

Quotations / Sales Orders
-------------------------

1. Create or open a quotation.
2. Select the Sales Team.
3. If the team has bank accounts configured, the field *Team bank account*
   becomes available.
4. Choose the desired bank account.
5. When printing the quotation, the selected bank account is displayed in the
   PDF, after totals.

Customer Invoices
-----------------

1. Create or open a customer invoice (or customer credit note).
2. Select the Sales Team.
3. The field *Recipient Bank* (``partner_bank_id``) is restricted to the bank
   accounts configured on the selected Sales Team.
4. If the invoice is created from a quotation, the selected bank account on the
   quotation is copied automatically to the invoice.
5. When printing the invoice, the selected bank account is displayed in the PDF,
   after totals.

Notes
=====

- The module reuses the standard invoice field ``partner_bank_id`` and limits
  its available values based on the selected Sales Team.
- Bank account selection on quotations is stored in
  ``sale.order.partner_bank_id`` and is propagated to invoices when they are 
  generated from sales orders.
- If a Sales Team has only one bank account configured, the module auto-selects
  it on change.
- If the selected bank account is not allowed for the chosen Sales Team, the
  module prevents saving the document.

Credits
=======

Author
~~~~~~

.. image:: https://trey.es/logo.png
   :alt: Trey, Kilobytes de Soluciones S.L.
`Trey, Kilobytes de Soluciones <https://www.trey.es>`_
