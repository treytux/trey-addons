###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    unit_balance = fields.Float(
        string='Quantity balance',
        compute='_compute_unit_balance',
        store=True,
    )

    @api.depends('line_ids', 'line_ids.unit_amount', 'line_ids.task_id')
    def _compute_unit_balance(self):
        for line in self:
            line.unit_balance = sum([ln.unit_balance for ln in line.line_ids])
