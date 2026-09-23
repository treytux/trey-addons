###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase


class TestAccountInvoiceDateAutoConfirm(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.company = self.env.ref('base.main_company')
        self.income_account = self.env['account.account'].create({
            'name': 'Test Income',
            'code': 'TSTINC2',
            'account_type': 'income',
            'company_id': self.company.id,
        })
        self.product = self.env['product.template'].create({
            'name': 'Test Product',
            'type': 'service',
            'property_account_income_id': self.income_account.id,
            'company_id': self.company.id,
        }).product_variant_id
        self.today = fields.Date.context_today(self.env['account.move'])

    def _create_invoice(self, invoice_date, with_lines=True):
        vals = {
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_date': invoice_date,
        }
        if with_lines:
            vals['invoice_line_ids'] = [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })]
        return self.env['account.move'].create(vals)

    def test_confirms_invoice_with_today_date(self):
        invoice = self._create_invoice(self.today)
        self.env['account.move']._cron_auto_confirm_draft_invoices()
        self.assertEqual(invoice.state, 'posted')

    def test_does_not_confirm_future_date(self):
        invoice = self._create_invoice(self.today + timedelta(days=1))
        self.env['account.move']._cron_auto_confirm_draft_invoices()
        self.assertEqual(invoice.state, 'draft')

    def test_does_not_confirm_past_date_by_default(self):
        invoice = self._create_invoice(self.today - timedelta(days=1))
        self.env['account.move']._cron_auto_confirm_draft_invoices()
        self.assertEqual(invoice.state, 'draft')

    def test_confirms_past_date_when_flag_true(self):
        invoice = self._create_invoice(self.today - timedelta(days=1))
        self.env['account.move']._cron_auto_confirm_draft_invoices(
            confirm_past_date=True)
        self.assertEqual(invoice.state, 'posted')

    def test_error_on_confirm_is_caught_and_logged(self):
        invoice = self._create_invoice(self.today, with_lines=False)
        self.env['account.move']._cron_auto_confirm_draft_invoices()
        self.assertEqual(invoice.state, 'draft')
