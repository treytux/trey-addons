###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    picking_state = fields.Selection(
        selection=[('completed', 'Fully Delivered'),
                   ('partial', 'Partial Delivered'),
                   ('no', 'Nothing Delivered')],
        string='Picking Status',
        compute='_compute_picking_state',
        store=True,
        readonly=True,
        default='no')

    @api.depends('state', 'product_uom_qty', 'qty_delivered')
    def _compute_picking_state(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for line in self:
            if line.product_id.type != 'product':
                line.picking_state = 'completed'
                continue
            compare = float_compare(
                line.qty_delivered, line.product_uom_qty,
                precision_digits=precision)
            if compare == 0:
                line.picking_state = 'completed'
            elif compare == -1:
                line.picking_state = 'partial'
            else:
                line.picking_state = 'no'
