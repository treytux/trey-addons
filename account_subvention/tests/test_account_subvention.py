###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountSubvention(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name' : 'Partner test',
        })
        self.currency = self.env.ref('base.EUR')
        self.subvention = self.env['account.subvention'].create({
            'name': 'Subvention',
            'partner_id' : self.partner.id,
            'journal_id' : 1,
            'account_id' : 0,
        })
        tax_group = self.env['account.tax.group'].create({
            'name': 'taxes',
        })
        tax = self.env['account.tax'].create({
            'name': '10% Tax',
            'amount_type': 'percent',
            'amount': 10,
            'type_tax_use' : 'sale',
            'tax_group_id' : tax_group.id,
        })
        product = self.env['product.product'].create({
            'name': 'Service product',
            'type': 'service',
            'company_id': False,
            'list_price': 100,
            'subvention_ok': True,
            'taxes_id': [(6, 0, [tax.id])],
        })
        type_revenue = self.env.ref('account.data_account_type_revenue')
        account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': account_sale.id,
            'default_credit_account_id': account_sale.id,
            'update_posted': True,
        })
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'price_unit': product.list_price,
                'account_id': account_sale.id,
                'quantity': 1,
                'subvention_id': self.subvention.id,
            })],
        })

    def test_onchange_product_id_assign_subvention(self):
        self.assertEqual(self.invoice.invoice_line_ids.subvention_id, self.subvention)

    def test_validate_invoice(self):
        self.invoice.action_move_create()
        self.assertTrue(self.invoice.move_id, msg='No hay journal entries creadas')

    def test_validate_invoice_without_invoice_line(self):
        self.invoice.invoice_line_ids = None
        with self.assertRaises(UserError):
            self.invoice.action_move_create()

    def test_validate_payment(self):
        self.invoice.invoice_line_ids._onchange_product_id()
        self.invoice._onchange_invoice_line_ids()
        self.invoice.action_invoice_open()
        self.assertEquals(self.invoice.state, 'open')
        payment = self.env['account.payment'].create({
            'invoice_ids': [(4, self.invoice.id)],
            'partner_id': self.partner.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'journal_id': self.journal.id,
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'amount': self.invoice.amount_total,
        })
        payment.action_validate_invoice_payment()
        self.assertEquals(self.invoice.state, 'paid')
