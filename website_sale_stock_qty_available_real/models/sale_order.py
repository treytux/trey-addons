###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _website_sale_stock_qty_mode(self):
        self.ensure_one()
        if not self.website_id:
            return 'available'
        return self.website_id._get_website_sale_stock_qty_mode()

    def _get_context_for_line(self, line):
        res = super()._get_context_for_line(line)
        mode = self._website_sale_stock_qty_mode()
        if mode != 'available':
            res['website_sale_stock_qty_mode'] = mode
        return res

    def _cart_update(self, product_id=None, line_id=None, add_qty=0,
                     set_qty=0, **kwargs):
        order = self
        mode = self._website_sale_stock_qty_mode()
        if mode != 'available':
            order = order.with_context(website_sale_stock_qty_mode=mode)
        return super(SaleOrder, order)._cart_update(
            product_id, line_id, add_qty, set_qty, **kwargs)
