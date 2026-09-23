###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountSubvention(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name' : 'Partner test',
        })
        self.currency = self.currency = self.env.ref('base.EUR')
        self.subvention = self.env['account.subvention'].create({
            'name': 'Subvention',
            'partner_id': self.partner.id,
            'journal_id': 1,
            'account_id': 0,
        })
        tax_group = self.env['account.tax.group'].create({
            'name': 'taxes',
        })
        tax = self.env['account.tax'].create({
            'name': '10% Tax',
            'amount_type': 'percent',
            'amount': 10,
            'type_tax_use': 'sale',
            'tax_group_id': tax_group.id,
        })
        product = self.env['product.product'].create({
            'name': 'Service product',
            'type': 'service',
            'company_id': False,
            'list_price': 100,
            'subvention_ok': True,
            'taxes_id': [(6, 0, [tax.id])],
        })
        account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': '700XXX',
            'account_type': 'income',
            'reconcile': True,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_account_id': account_sale.id,
        })
        self.invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': product.id,
                    'name': 'test',
                    'price_unit': 100,
                    'subvention_id': self.subvention.id,
                }),
            ]
        })

    def test_onchange_product_id_assign_subvention(self):
        self.assertEqual(
            self.invoice.invoice_line_ids.subvention_id, self.subvention)

    def test_validate_invoice(self):
        self.invoice.action_post()

    def test_validate_invoice_without_invoice_line(self):
        self.invoice.invoice_line_ids = None
        with self.assertRaises(UserError):
            self.invoice.action_post()
