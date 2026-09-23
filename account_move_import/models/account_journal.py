###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    import_account_moves = fields.Boolean(
        string='Import account moves',
    )
