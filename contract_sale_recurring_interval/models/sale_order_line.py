###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    recurring_interval = fields.Integer(
        default=1,
        string='Invoice Every',
        help='Invoice every (Days/Week/Month/Year)',
    )

    def _prepare_contract_line_values(self, contract,
                                      predecessor_contract_line_id=False):
        res = super()._prepare_contract_line_values(
            contract,
            predecessor_contract_line_id=predecessor_contract_line_id)
        res['recurring_interval'] = self.recurring_interval
        return res
