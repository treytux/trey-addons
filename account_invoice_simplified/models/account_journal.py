###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    journal_simplified_id = fields.Many2one(
        comodel_name='account.journal',
        string='Simplified invoice journal',
        domain='[("type", "=", "sale"), '
               '("journal_simplified_id", "=", False)]',
        help='Switch to this journal when an invoice is validated and the '
             'partner does not have VAT',
    )
