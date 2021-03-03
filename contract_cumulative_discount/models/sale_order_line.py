###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_contract_line_values(self, contract,
                                      predecessor_contract_line_id=False):
        res = super()._prepare_contract_line_values(
            contract,
            predecessor_contract_line_id=predecessor_contract_line_id)
        res.update({
            'multiple_discount': self.multiple_discount,
            'discount_name': self.discount_name,
        })
        return res
