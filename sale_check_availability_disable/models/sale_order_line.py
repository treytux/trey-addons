###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        ref = 'sale_check_availability_disable.show_availability_sale_warning'
        if self.env.user.has_group(ref):
            return super()._onchange_product_id_check_availability()
        return {}
