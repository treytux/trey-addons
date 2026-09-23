################################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    simplified_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Simplified Journal',
        help='If set, invoices imported without customer VAT will be '
             'created in this journal instead of the original one.',
    )
