###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
        domain="[('state', '=', 'open')]",
    )
    amount_signed = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        compute='_compute_sign_taxes',
        readonly=True,
        store=True,
    )

    @api.depends('amount', 'payment_type')
    def _compute_sign_taxes(self):
        for payment in self:
            sign = payment.payment_type in ['inbound', 'transfer'] and 1 or -1
            payment.amount_signed = payment.amount * sign
