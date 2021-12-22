###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    qty_total = fields.Float(
        string='Total units',
        compute='_compute_qty_total',
        help='Total units of the selected products.',
    )

    @api.depends('order_line')
    def _compute_qty_total(self):
        for order in self:
            order.qty_total = sum(order.order_line.filtered(
                lambda l: l.product_id.add_to_sum_qty).mapped(
                'product_uom_qty'))
