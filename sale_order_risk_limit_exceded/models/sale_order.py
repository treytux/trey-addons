###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_risk_sale_order_limit_exceded = fields.Boolean(
        string='Risk sale order limit exceded',
    )

    def risk_exception_msg(self):
        self.ensure_one()
        res = super().risk_exception_msg()
        self.is_risk_sale_order_limit_exceded = bool(res)
        return res
