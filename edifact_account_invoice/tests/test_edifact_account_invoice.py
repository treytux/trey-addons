# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields
import openerp.tests.common as common


class TestEdifactAccountInvoice(common.TransactionCase):

    def setUp(self):
        super(TestEdifactAccountInvoice, self).setUp()
        self.edifact_document1 = self.env['edifact.document'].create({
            'name': 'test',
            'ttype': 'invoice'})
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'zip': '18001',
            'city': 'Granada',
            'phone': '666225522',
            'ean13': '8422416000016',
            'vat': 'ESA28017895'})
        self.product_01 = self.env['product.product'].create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1',
            'list_price': 10})
        self.taxs_21 = self.env['account.tax'].search([
            ('name', 'like', '%21%'),
            ('company_id', '=', self.ref('base.main_company'))])
        self.account_01 = self.env['account.account'].search([
            ('code', '=', '700000'),
            ('company_id', '=', self.ref('base.main_company'))])
        self.invoice_01 = self.env['account.invoice'].create({
            'partner_id': self.partner_01.id,
            'reference_type': 'none',
            'company_id': self.ref('base.main_company'),
            'type': 'out_invoice',
            'account_id': self.account_01.id,
            'origin': 'SO076',
            'date_invoice': fields.Date.today(),
            'date_due': fields.Date.today()})
        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.product_01.product_tmpl_id.list_price,
            'price_subtotal': self.product_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.product_01.id,
            'quantity': 1,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'})
        self.invoice_line_02 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.product_01.product_tmpl_id.list_price,
            'price_subtotal': self.product_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.product_01.id,
            'quantity': 5,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'})

    def test_export_invoices(self):
        self.invoice_01.signal_workflow('invoice_open')
        self.edifact_document1.process_invoice_out_files(
            self.invoice_01)
