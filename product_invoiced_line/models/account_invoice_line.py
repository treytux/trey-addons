# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    inv_state = fields.Selection(
        string='Invoice State',
        related='invoice_id.state',
        store=True)
    inv_date = fields.Date(
        string='Invoice Date',
        related='invoice_id.date_invoice',
        store=True)
