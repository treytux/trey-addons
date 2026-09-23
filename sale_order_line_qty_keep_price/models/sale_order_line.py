###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        prices_before = {line.id: line.price_unit for line in self}
        super()._compute_price_unit()
        for line in self:
            if line.id in prices_before and prices_before[line.id] > 0.0:
                if (not line._origin
                        or line._origin.product_id.id == line.product_id.id):
                    line.price_unit = prices_before[line.id]
