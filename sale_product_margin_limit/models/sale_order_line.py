###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def is_limit_ok(self):
        res = super().is_limit_ok()
        if not res or not self.product_id:
            return res
        if self.env.user.ignore_margin_price_limit:
            return res
        price_unit = self.price_subtotal / self.product_uom_qty
        if price_unit >= self.product_id.margin_price_limit:
            return res
        self.order_id.exception_limit_reason = _(
            'The product "%s" is selling below its minimum sale price '
            'unit %s' % (
                self.product_id.name, self.product_id.margin_price_limit))
        return False
