###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
        domain='[(\'state\', \'=\', \'open\')]',
    )
    amount_signed = fields.Monetary(
        string='Amount signed',
        currency_field='currency_id',
        compute='_compute_sign_taxes',
        readonly=True,
        store=True,
    )
    force_session_outstanding_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Force session outstanding Account',
        check_company=True,
    )

    @api.depends('force_session_outstanding_account_id')
    def _compute_outstanding_account_id(self):
        super()._compute_outstanding_account_id()
        for payment in self:
            if payment.force_session_outstanding_account_id:
                payment.outstanding_account_id = (
                    payment.force_session_outstanding_account_id)

    @api.depends('amount', 'payment_type')
    def _compute_sign_taxes(self):
        for payment in self:
            sign = payment.payment_type in ['inbound', 'transfer'] and 1 or -1
            payment.amount_signed = payment.amount * sign

    def action_post(self):
        if (self.env.user.has_group('sale_session.group_user_sale_session')
                and not self.env.user.has_group('account.group_account_invoice')
                and self.payment_id.sale_session_id):
            return super(AccountPayment, self.sudo()).action_post()
        return super().action_post()
