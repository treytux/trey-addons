###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSaleOrderConfirmRequirePayment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })
        self.payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment Term',
        })
        method_in = self.env.ref('account.account_payment_method_manual_in')
        journal = self.env['account.journal'].create({
            'name': 'Test Bank',
            'code': 'TBNK',
            'type': 'bank',
            'company_id': self.company.id,
        })
        self.payment_mode = self.env['account.payment.mode'].create({
            'name': 'Test Payment Mode',
            'bank_account_link': 'variable',
            'payment_method_id': method_in.id,
            'company_id': self.company.id,
            'fixed_journal_id': journal.id,
            'variable_journal_ids': [(6, 0, [journal.id])],
        })

    def create_sale(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })],
        })
        sale.payment_term_id = False
        sale.payment_mode_id = False
        return sale

    def test_confirm_without_payment_data_raises(self):
        sale = self.create_sale()
        with self.assertRaises(ValidationError):
            sale.action_confirm()
        self.assertNotEqual(sale.state, 'sale')

    def test_confirm_only_payment_term_raises(self):
        sale = self.create_sale()
        sale.payment_term_id = self.payment_term.id
        with self.assertRaises(ValidationError):
            sale.action_confirm()
        self.assertNotEqual(sale.state, 'sale')

    def test_confirm_only_payment_mode_raises(self):
        sale = self.create_sale()
        sale.payment_mode_id = self.payment_mode.id
        with self.assertRaises(ValidationError):
            sale.action_confirm()
        self.assertNotEqual(sale.state, 'sale')

    def test_confirm_with_both_payment_data_succeeds(self):
        sale = self.create_sale()
        sale.payment_term_id = self.payment_term.id
        sale.payment_mode_id = self.payment_mode.id
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
