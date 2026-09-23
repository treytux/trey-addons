###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    subvention_percent = fields.Float(
        string='Subvention (%)',
    )
    subvention_id = fields.Many2one(
        comodel_name='account.subvention',
        string='Subvention',
    )

    def cron_reconcile_account_move_lines_subvention(self):
        move_lines2reconcile = self.search([
            ('subvention_id', '!=', False),
            ('reconciled', '=', False),
        ])
        for move_line in move_lines2reconcile:
            move_line.action_subvention_reconcile()
