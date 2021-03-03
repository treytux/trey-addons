###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    discount = fields.Integer(
        string='Discount %',
    )
