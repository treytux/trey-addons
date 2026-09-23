###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'company_id', 'currency_id', 'product_uom')
    def _compute_purchase_price(self):
        super()._compute_purchase_price()
        for line in self:
            if (not line.product_id.pack_ok
                    and line.pack_parent_line_id.product_id.pack_component_cost
                    in ['totalized', 'ignored']):
                line.purchase_price = 0.0
