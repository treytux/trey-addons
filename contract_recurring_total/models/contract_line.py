###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    recurring_subtotal = fields.Float(
        string='Recurring Subtotal',
        compute='_compute_recurring_subtotal',
    )

    @api.depends('price_unit', 'quantity', 'state', 'recurring_rule_type')
    def _compute_recurring_subtotal(self):
        rule_type_dict = {
            'daily': 365,
            'weekly': 52,
            'monthly': 12,
            'monthlylastday': 12,
            'quarterly': 4,
            'semesterly': 2,
        }
        for line in self.filtered(lambda cl: cl.state != 'canceled'):
            rule_type = rule_type_dict.get(line.recurring_rule_type, 1)
            line.recurring_subtotal = (
                line.price_unit * rule_type) * line.quantity
