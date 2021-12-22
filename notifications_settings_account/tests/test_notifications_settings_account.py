###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestNotificationsSettingsAccount(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'product',
            'list_price': 10,
        })
        self.bank = self.env['account.journal'].create({
            'name': 'Bank',
            'type': 'bank',
            'code': 'BNK67',
        })
        self.currency_eur_id = self.env.ref('base.EUR').id
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ]
        })
        website = self.env['website'].create({
            'name': 'new website',
        })
        self.sale.website_id = website

    def test_notify_invoice_open(self):
        self.sale.website_id.notify_invoice_open = True
        self.sale.action_confirm()
        self.sale.action_invoice_create()
        last_message = self.sale.invoice_ids[0].message_ids[0]
        self.assertNotIn(
            'Please remit payment at your earliest convenience.',
            last_message.body)
        message_ids_tam = len(self.sale.invoice_ids[0].message_ids)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        last_message = self.sale.invoice_ids[0].message_ids[0]
        self.assertIn(
            'Please remit payment at your earliest convenience.',
            last_message.body)
        self.assertNotEqual(message_ids_tam, len(self.sale.message_ids))

    def test_notify_invoice_paid(self):
        self.sale.website_id.notify_invoice_paid = True
        self.sale.action_confirm()
        self.sale.action_invoice_create()
        message_ids_tam = len(self.sale.invoice_ids[0].message_ids)
        invoice = self.sale.invoice_ids[0]
        invoice.action_invoice_open()
        last_message = self.sale.invoice_ids[0].message_ids[0]
        self.assertNotIn(
            'Please remit payment at your earliest convenience.',
            last_message.body)
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'partner_type': 'customer',
            'partner_id': self.partner.id,
            'amount': 100,
            'currency_id': self.currency_eur_id,
            'journal_id': self.bank.id,
            'payment_date': fields.Date.today(),
            'invoice_ids': [(6, 0, self.sale.invoice_ids.ids)],
        })
        payment.action_validate_invoice_payment()
        last_message = self.sale.invoice_ids[0].message_ids[0]
        self.assertIn('This invoice is already paid.', last_message.body)
        self.assertNotEqual(message_ids_tam, len(invoice.message_ids))
