###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_propagated_comment = fields.Text(
        string='Sale Propagated Comment',
        compute='_compute_sale_comment',
    )

    @api.depends('move_lines', 'move_lines.sale_line_id')
    def _compute_sale_comment(self):
        for picking in self:
            comments = picking.move_lines.mapped(
                'sale_line_id.order_id.sale_propagated_comment')
            picking.sale_propagated_comment = '\n'.join(
                c for c in comments if c)
