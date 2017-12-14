# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice.line'
    _order = 'invoice_id,id'
