from odoo.tests.common import TransactionCase


class TestAccountMoveLineFromPartner(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_12')
        self.product = self.env.ref('product.product_product_4d')
        self.account_sale = self.env.ref('l10n_generic_coa.1_conf_a_sale')
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })

    def create_and_pay_invoice(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': self.product.lst_price,
                'account_id': self.account_sale.id,
                'quantity': 1})],
        })
        invoice.action_invoice_open()
        payment = self.env['account.payment'].create({
            'invoice_ids': [(4, invoice.id)],
            'partner_id': self.partner.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'journal_id': self.journal.id,
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'amount': invoice.amount_total,
        })
        payment.action_validate_invoice_payment()

    def test_01_account_move_line_from_partner(self):
        account_move_count = self.partner.account_move_line_count
        self.assertEqual(
            self.partner.account_move_line_count, account_move_count)
        self.create_and_pay_invoice()
        self.assertEqual(
            self.partner.account_move_line_count, account_move_count + 4)
        self.create_and_pay_invoice()
        self.assertEqual(
            self.partner.account_move_line_count, account_move_count + 8)
