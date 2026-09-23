###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductPackLine(models.Model):
    _inherit = 'product.pack.line'

    def get_sale_order_line_vals(self, line, order):
        res = super().get_sale_order_line_vals(line, order)
        if line.pack_parent_line_id.product_id.pack_component_cost == 'detailed':
            return res
        if (line.pack_parent_line_id.product_id.pack_component_cost
                in ['totalized', 'ignored']):
            res['purchase_price'] = 0.0
        return res
