###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        return super(
            SaleOrderLine, self.filtered(
                lambda line: line.product_id.pack_ok is False)
        )._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty)
