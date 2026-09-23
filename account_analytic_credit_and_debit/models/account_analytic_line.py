###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    debit = fields.Monetary(
        string='Debit',
        compute='_compute_debit_credit',
        store=True,
        precompute=True,
    )
    credit = fields.Monetary(
        string='Credit',
        compute='_compute_debit_credit',
        store=True,
        precompute=True,
    )

    @api.depends('amount')
    def _compute_debit_credit(self):
        for line in self:
            line.debit = -line.amount if line.amount < 0.0 else 0.0
            line.credit = line.amount if line.amount > 0.0 else 0.0
