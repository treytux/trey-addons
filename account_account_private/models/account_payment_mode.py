###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    restrict_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='account_payment_mode2res_users_rel',
        column1='payment_mode_id',
        column2='user_id',
        help='Restrict access to this users, empty for public payment mode.',
    )
