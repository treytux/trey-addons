###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    confirm_orders_automatically = fields.Boolean(
        string='Confirm orders automatically',
        help='Confirm sales orders automatically after the customer selects '
             'this payment provider.',
    )
