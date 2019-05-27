###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    picking_state = fields.Selection(
        selection=[('completed', 'Fully Delivered'),
                   ('partial', 'Partial Delivered'),
                   ('no', 'Nothing Delivered')],
        string='Picking Status',
        compute='_compute_picking_state',
        store=True,
        readonly=True)

    @api.depends('state', 'order_line.picking_state')
    def _compute_picking_state(self):
        for order in self:
            order.picking_state = 'no'
            if order.state not in ('sale', 'done'):
                continue
            line_picking_state = set([
                line.picking_state for line in order.order_line])
            if 'partial' in line_picking_state:
                order.picking_state = 'partial'
            elif line_picking_state == {'completed'}:
                order.picking_state = 'completed'
