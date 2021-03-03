###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    purchase_propagated_comment = fields.Text(
        string='Purchase Propagated Comment',
        compute='_compute_purchase_comment',
    )

    @api.depends('move_lines', 'move_lines.purchase_line_id')
    def _compute_purchase_comment(self):
        for picking in self:
            comments = picking.move_lines.mapped(
                'purchase_line_id.order_id.purchase_propagated_comment')
            picking.purchase_propagated_comment = '\n'.join(
                c for c in comments if c)
