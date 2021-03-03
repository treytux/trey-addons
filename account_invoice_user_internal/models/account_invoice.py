# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    user_id = fields.Many2one(
        domain=[('share', '=', False)],
    )
