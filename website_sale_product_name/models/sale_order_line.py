###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api
from odoo.addons.website_sale.models.sale_order_line import \
    SaleOrderLine as WebsiteSaleOrderLine


class SaleOrderLine(WebsiteSaleOrderLine):
    _inherit = 'sale.order.line'

    @api.depends('product_id.display_name')
    def _compute_name_short(self):
        for record in self:
            record.name_short = (
                record.product_id.public_name
                or super()._compute_name_short())
