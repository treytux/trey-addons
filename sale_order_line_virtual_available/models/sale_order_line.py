###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    virtual_available = fields.Float(
        compute='_compute_virtual_available',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Virtual available',
    )

    @api.depends('product_id', 'order_id.warehouse_id')
    def _compute_virtual_available(self):
        for line in self:
            line.virtual_available = line.product_id.with_context(
                warehouse=line.order_id.warehouse_id.id).virtual_available
