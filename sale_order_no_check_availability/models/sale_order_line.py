###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        group = self.env.ref(
            'sale_order_no_check_availability.group_check_availability')
        res = super()._onchange_product_id_check_availability()
        if self.env.user not in group.users:
            res.pop('warning', None)
        return res
