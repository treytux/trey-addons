###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_changed')
    def _compute_picking_state(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        super()._compute_picking_state()
        for line in self:
            if not line.order_id.is_return:
                continue
            if line.product_id.type != 'product':
                continue
            qty_change = float_compare(
                line.qty_change, line.qty_changed,
                precision_digits=precision)
            qty_returned = float_compare(
                line.product_uom_qty, line.qty_returned,
                precision_digits=precision)
            if qty_change == 0 and qty_returned == 0:
                line.picking_state = 'completed'
            elif qty_change == 0 or qty_returned == 0:
                line.picking_state = 'partial'
            elif qty_change == -1 or qty_returned == -1:
                line.picking_state = 'partial'
            else:
                line.picking_state = 'no'
