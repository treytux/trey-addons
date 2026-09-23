###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    payment_provider_ids = fields.One2many(
        comodel_name='payment.provider',
        inverse_name='payment_mode_id',
        string='Payment providers',
    )
