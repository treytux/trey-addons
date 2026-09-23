###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import SavepointCase


class TestInvoicewarnings(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_type = cls.env['account.account.type'].create({
            'name': 'Test User Type',
        })
        cls.account = cls.env['account.account'].create({
            'name': 'Test Account',
            'code': '600',
            'user_type_id': user_type.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

    def test_company_not_checked(self):
        """Test if warnings are not shown"""
        self.env.user.company_id.show_wrong_accounts = False
        self.env.user.company_id.show_wrong_taxes = False
        self.env.user.company_id.show_wrong_vat = False
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1.0,
                'price_unit': 1.0,
                'account_id': self.account.id,
            })]
        })
        self.assertEqual(invoice.wrong_taxes, False)
        self.assertEqual(invoice.wrong_account, False)
        self.assertEqual(invoice.wrong_vat, False)

    def test_company_checked(self):
        """Test if warnings are shown"""
        self.env.user.company_id.show_wrong_accounts = True
        self.env.user.company_id.show_wrong_taxes = True
        self.env.user.company_id.show_wrong_vat = True
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1.0,
                'price_unit': 1.0,
                'account_id': self.account.id,
            })]
        })
        self.assertEqual(invoice.wrong_taxes, True)
        self.assertEqual(invoice.wrong_account, True)
        self.assertEqual(invoice.wrong_vat, True)
