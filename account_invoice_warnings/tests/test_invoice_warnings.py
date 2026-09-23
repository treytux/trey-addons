###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestInvoicewarnings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.env['account.account'].create({
            'name': 'Test Account',
            'code': '600',
        })
        cls.receivable_account = cls.env['account.account'].create({
            'name': 'Test Receivable Account',
            'code': '430000',
            'account_type': 'asset_receivable',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.partner.property_account_receivable_id = cls.receivable_account
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test Sales Journal',
            'type': 'sale',
            'code': 'TSAL',
            'company_id': cls.env.company.id,
        })

    def test_company_not_checked(self):
        self.env.company.show_wrong_accounts = False
        self.env.company.show_wrong_taxes = False
        self.env.company.show_wrong_vat = False
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1.0,
                'price_unit': 1.0,
                'account_id': self.account.id,
            })],
        })
        self.assertEqual(invoice.wrong_taxes, False)
        self.assertEqual(invoice.wrong_account, False)
        self.assertEqual(invoice.wrong_vat, False)

    def test_company_checked(self):
        self.env.company.show_wrong_accounts = True
        self.env.company.show_wrong_taxes = True
        self.env.company.show_wrong_vat = True
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1.0,
                'price_unit': 1.0,
                'account_id': self.account.id,
                'tax_ids': [(6, 0, [])],
            })],
        })
        self.assertEqual(invoice.wrong_taxes, True)
        self.assertEqual(invoice.wrong_account, True)
        self.assertEqual(invoice.wrong_vat, True)
