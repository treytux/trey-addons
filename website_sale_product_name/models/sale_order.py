###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api
from odoo.addons.website_sale.models.sale_order import \
    SaleOrder as WebsiteSaleOrder


class SaleOrder(WebsiteSaleOrder):
    _inherit = 'sale.order'

    @api.model
    def _cart_update_order_line(self, product_id, quantity, order_line, **kwargs):
        order_line = super()._cart_update_order_line(
            product_id, quantity, order_line, **kwargs)
        if order_line:
            order_line.name = (
                order_line.product_id.public_name or order_line.name)
        return order_line
