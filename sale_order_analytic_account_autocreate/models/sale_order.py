###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super()._action_confirm()
        for order in self:
            if (order.company_id.autocreate_sale_analytic_account
                    and not order.analytic_account_id):
                order._create_analytic_account()
        return res
