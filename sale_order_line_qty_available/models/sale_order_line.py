###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float(
        compute='_compute_qty_available',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Quantity On Hand')

    @api.one
    @api.depends('product_id', 'order_id.warehouse_id')
    def _compute_qty_available(self):
        self.qty_available = self.product_id.with_context(
            warehouse=self.order_id.warehouse_id.id).qty_available
