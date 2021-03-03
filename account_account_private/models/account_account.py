###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    restrict_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='account_account2res_users_rel',
        column1='account_id',
        column2='user_id',
        help='Restrict access to this users, empty for public account',
    )
