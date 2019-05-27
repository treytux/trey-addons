###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _compute_amount_total_without_delivery(self):
        self.ensure_one()
        delivery_cost = sum([
            l.price_subtotal for l in self.order_line if l.is_delivery])
        return self.amount_untaxed - delivery_cost
