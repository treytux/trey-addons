###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        payments = super()._create_payments()
        if len(payments) != 1:
            raise UserError(_(
                'You can only process one payment at a time with this payment '
                'method.'))
        if (not self.payment_method_line_id
                or self.payment_method_line_id.payment_provider_id.code
                != 'instore'):
            return payments
        if (self.env.context.get('active_model') != 'account.move'
                or not self.env.context.get('active_id')):
            raise UserError(_(
                'With this payment method, you need process payments from '
                'invoices.'))
        invoice = self.env['account.move'].browse(
            self.env.context['active_ids'][0])
        payment_method = self.payment_method_line_id.payment_method_id
        if payments.payment_type == 'inbound':
            payment_method.pay_instore_tpv(
                self.payment_method_line_id.payment_provider_id, payments,
                invoice)
        elif payments.payment_type == 'outbound':
            if not invoice.reversed_entry_id:
                raise UserError(_('You need to reverse the invoice before.'))
            payment_method.refund_instore_tpv(
                self.payment_method_line_id.payment_provider_id, payments,
                invoice)
        return payments
