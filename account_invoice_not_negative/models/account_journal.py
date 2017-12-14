# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class Journal(models.Model):
    _inherit = 'account.journal'

    allow_invoice_negative = fields.Boolean(
        string='Allow to validate negative invoices',
        default=True)
