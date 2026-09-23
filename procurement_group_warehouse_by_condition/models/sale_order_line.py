###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = super()._onchange_product_id_check_availability()
        is_hide_msg = (
            self.order_id.warehouse_id.is_warehouse_by_condition
            and res.get('warning', False)
            and res.get('warning').get('title', False)
            and _('Not enough inventory!') in res.get('warning').get('title'))
        if is_hide_msg:
            res['warning'] = ''
        return res
