###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PartnerEarlyPaymentDiscount(models.Model):
    _name = 'partner.early.payment.discount'
    _description = 'Partner early payment discount'

    name = fields.Char(
        string='Name',
        required=True,
    )
    discount = fields.Float(
        string='% Discount',
        required=True,
        help='Early Payment Discount in %.',
    )
