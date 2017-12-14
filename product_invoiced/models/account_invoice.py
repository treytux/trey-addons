# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields
import logging
_log = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    date_invoice = fields.Date(
        string='Date invoice',
        related='invoice_id.date_invoice',
        store=True,
        readonly=True)
    date_due = fields.Date(
        string='Date due',
        related='invoice_id.date_due',
        store=True,
        readonly=True)
