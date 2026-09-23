###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    stock_info = fields.Char(
        string='Stock info',
        compute='_compute_stock_info',
    )

    @api.depends('product_id', 'order_id.picking_type_id')
    def _compute_stock_info(self):
        for line in self:
            stock_info = {
                _('On hand'): line.product_id.qty_available,
                _('Stock real'): line.product_id.qty_available_real,
                _('Order warehouse'): line.qty_available_real,
            }
            line.stock_info = ','.join(
                [f'{key}: {value}' for key, value in stock_info.items()])
