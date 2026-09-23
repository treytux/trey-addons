###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_propagated_comment = fields.Text(
        string='Sale Propagated Comment',
        compute='_compute_sale_comment',
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.sale_line_ids')
    def _compute_sale_comment(self):
        for move in self:
            comments = move.invoice_line_ids.mapped(
                'sale_line_ids.order_id.sale_propagated_comment')
            move.sale_propagated_comment = '\n'.join(
                c for c in comments if c)
