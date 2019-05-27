###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    def action_revert_to_draft(self):
        for move in self.move_lines:
            move.state = 'draft'
        self.state = 'draft'
