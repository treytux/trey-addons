###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('direct_order', 'Direct payment')],
    )

    automatic_reconcile = fields.Boolean(
        string='Automatic reconcile',
        help="The account move is automatically generated and reconciled.",
        default=True,
    )

    @api.model
    def direct_order_get_form_action_url(self):
        return '/payment/direct_order/feedback'
