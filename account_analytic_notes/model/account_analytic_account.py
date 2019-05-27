###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    notes = fields.Text(
        string='Internal notes',
        help='Type contract internal comments. '
             'This text will not be shown in contract invoices.')
