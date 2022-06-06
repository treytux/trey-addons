###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        super().product_id_change()
        self.discount = sum(
            self.mapped('order_id.global_discount_ids.total_percent'))
