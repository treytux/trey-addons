###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    account_move_line_count = fields.Integer(
        string='Account move line count',
        compute='_compute_account_move_line_count'
    )

    @api.multi
    def _compute_account_move_line_count(self):
        for partner in self:
            move_lines = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id)])
            partner.account_move_line_count = len(move_lines)
