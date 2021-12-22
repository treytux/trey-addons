###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    payment_acquirer_ids = fields.One2many(
        comodel_name='payment.acquirer',
        inverse_name='payment_mode_id',
        string='Payment acquirers',
    )
