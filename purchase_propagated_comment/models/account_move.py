###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_propagated_comment = fields.Text(
        string='Purchase Propagated Comment',
        compute='_compute_purchase_comment',
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.purchase_line_id')
    def _compute_purchase_comment(self):
        for move in self:
            comments = move.invoice_line_ids.mapped(
                'purchase_line_id.order_id.purchase_propagated_comment')
            move.purchase_propagated_comment = '\n'.join(
                c for c in comments if c)
