###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    payment_mode_ids = fields.One2many(
        comodel_name='account.payment.mode',
        inverse_name='payment_acquirer_id',
        string='Show for payment modes',
        help='Customers with one of the following payment modes will see this'
        ' payment method. If nothing\'s selected, it will be available for'
        ' all customers.',
    )
