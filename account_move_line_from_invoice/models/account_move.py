###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_line_count = fields.Integer(
        string='Invoice line count',
        compute='_compute_invoice_line_count',
    )

    @api.depends('invoice_line_ids')
    def _compute_invoice_line_count(self):
        for move in self:
            move.invoice_line_count = len(move.invoice_line_ids)
