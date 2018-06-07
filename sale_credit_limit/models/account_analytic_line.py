# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields
import openerp.addons.decimal_precision as dp


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    amount_to_invoiced = fields.Float(
        compute='_compute_amount_to_invoiced',
        string='Total Amount Invoiced',
        digits=dp.get_precision('Account'))

    @api.depends('to_invoice', 'unit_amount', 'product_id', 'amount')
    def _compute_amount_to_invoiced(self):
        for line in self:
            line.amount_to_invoiced = line.amount - line.amount * (
                line.to_invoice.factor / 100)
