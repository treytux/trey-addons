###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    show_balance_warning = fields.Boolean(
        string='Show balance warning',
        help='Show warning in tasks when the analytic account balance is '
             'negative.',
        default=True,
    )
