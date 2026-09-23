###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for move in self:
            need_change_journal_to_simplified = bool(
                move.move_type in ['out_invoice', 'out_refund']
                and not move.partner_id.vat
                and move.journal_id != move.journal_id.journal_simplified_id
                and move.journal_id.journal_simplified_id)
            if need_change_journal_to_simplified:
                move.journal_id = move.journal_id.journal_simplified_id
        return super().action_post()
