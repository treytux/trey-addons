###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def recalculate_prices(self):
        res = super().recalculate_prices()
        for line in self.mapped('order_line'):
            line.recalculate_purchase_last_price()
        return res
