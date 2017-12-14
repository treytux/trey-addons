# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase
from openerp import fields, exceptions, _


class TestInvoiceDescriptionNumber(TransactionCase):
    def setUp(self):
        super(TestInvoiceDescriptionNumber, self).setUp()
        self.taxs_21 = self.env['account.tax'].search([
            ('name', '=', 'IVA 21%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_21.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'21\' in name.'))
        self.tax_21 = self.taxs_21[0]
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product',
            'list_price': 10,
            'taxes_id': [(6, 0, [self.tax_21.id])]})
        pp_01_data = {'product_tmpl_id': self.pt_01.id}
        self.pp_01 = self.env['product.product'].create(pp_01_data)
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'product',
            'list_price': 20,
            'taxes_id': [(6, 0, [self.tax_21.id])]})
        pp_02_data = {'product_tmpl_id': self.pt_02.id}
        self.pp_02 = self.env['product.product'].create(pp_02_data)
        accounts_430 = self.env['account.account'].search([
            ('code', '=', '430000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not accounts_430.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'430000\' code.'))
        account_430 = accounts_430[0]
        accounts_700 = self.env['account.account'].search([
            ('code', '=', '700000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not accounts_700.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'700000\' code.'))
        account_700 = accounts_700[0]
        payment_terms = self.env['account.payment.term'].search([])
        if not payment_terms.exists():
            raise exceptions.Warning(_('Does not exist any payment_term.'))
        self.invoice_01 = self.env['account.invoice'].create({
            'partner_id': self.partner_01.id,
            'type': 'out_invoice',
            'account_id': account_430.id,
            'date_invoice': fields.Date.today(),
            'payment_term': payment_terms[0].id})
        self.invoice_line_1_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'product_id': self.pp_01.id,
            'name': self.pp_01.name_template,
            'quantity': 1,
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'account_id': account_700.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])]})
        self.invoice_line_1_2 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'product_id': self.pp_02.id,
            'name': self.pp_02.name_template,
            'quantity': 3,
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'account_id': account_700.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])]})

    def test_01(self):
        self.invoice_01.button_reset_taxes()
        self.assertEqual(self.invoice_01.name, False)
        self.invoice_01.signal_workflow('invoice_open')
        self.assertEqual(self.invoice_01.state, 'open')
        self.assertEqual(self.invoice_01.name, self.invoice_01.number)
        move_lines = self.env['account.move.line'].search([
            ('invoice', '=', self.invoice_01.id)])
        for move_line in move_lines:
            self.assertEqual(move_line.ref, self.invoice_01.number)
