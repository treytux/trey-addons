###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestAccountInvoiceOpenCheck(TransactionCase):

    def setUp(self):
        super().setUp()
        domain = [('company_id', '=', self.env.ref('base.main_company').id)]
        if not self.env['account.account'].search_count(domain):
            _log.warn(
                'Test skipped because there is no chart of account defined')
            self.skipTest('No Chart of account found')
            return
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 50,
            'list_price': 50,
        })
        self.sale_journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale')], limit=1)
        self.account = self.env.user.company_id.get_chart_of_accounts_or_fail()
        self.fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position test',
        })

    def test_invoice_type_out_invoice(self):
        invoice_out = self.env['account.invoice'].create({
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        with self.assertRaises(ValidationError):
            invoice_out.action_invoice_open()
        invoice_out.partner_id.vat = '12345678Z'
        invoice_out.partner_shipping_id = self.partner.id
        invoice_out.fiscal_position_id = self.fiscal_position.id
        invoice_out.action_invoice_open()
        self.assertEquals(invoice_out.state, 'open')

    def test_invoice_type_out_refund(self):
        invoice_out_refund = self.env['account.invoice'].create({
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'type': 'out_refund',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        with self.assertRaises(ValidationError):
            invoice_out_refund.action_invoice_open()
        invoice_out_refund.partner_id.vat = '12345678Z'
        invoice_out_refund.partner_shipping_id = self.partner.id
        invoice_out_refund.fiscal_position_id = self.fiscal_position.id
        invoice_out_refund.action_invoice_open()
        self.assertEquals(invoice_out_refund.state, 'open')

    def test_invoice_type_in_invoice(self):
        invoice_in = self.env['account.invoice'].create({
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        with self.assertRaises(ValidationError):
            invoice_in.action_invoice_open()
        invoice_in.partner_id.vat = '12345678Z'
        invoice_in.partner_shipping_id = self.partner.id
        invoice_in.fiscal_position_id = self.fiscal_position.id
        invoice_in.action_invoice_open()
        self.assertEquals(invoice_in.state, 'open')

    def test_invoice_type_in_refund(self):
        invoice_in_refund = self.env['account.invoice'].create({
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'type': 'in_refund',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        with self.assertRaises(ValidationError):
            invoice_in_refund.action_invoice_open()
        invoice_in_refund.partner_id.vat = '12345678Z'
        invoice_in_refund.partner_shipping_id = self.partner.id
        invoice_in_refund.fiscal_position_id = self.fiscal_position.id
        invoice_in_refund.action_invoice_open()
        self.assertEquals(invoice_in_refund.state, 'open')
