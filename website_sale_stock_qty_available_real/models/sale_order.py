###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0,
                     set_qty=0, **kwargs):
        order = self.with_context(website_sale_stock_available=True)
        return super(SaleOrder, order)._cart_update(
            product_id, line_id, add_qty, set_qty, **kwargs)
