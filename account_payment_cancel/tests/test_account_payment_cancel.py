###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountPaymentCancel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale')], limit=1)
        self.payment = self.env['account.payment'].create({
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'sale_session_id': self.id,
            'amount': 100,
        })
        self.journal.update_posted = True
        self.payment.post()

    def test_cancel_payment(self):
        self.payment.cancel()
        self.assertEquals(self.payment.move_name, '')
