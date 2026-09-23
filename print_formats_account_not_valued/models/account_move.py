###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    show_valued_lines = fields.Boolean(
        string='Show Valued Lines',
        default=True,
        help='Show valued lines in the print view.',
    )
