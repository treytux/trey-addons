# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, exceptions, _
import re
import logging
_log = logging.getLogger(__name__)


class TestProductInvoiced(common.TransactionCase):

    def setUp(self):
        super(TestProductInvoiced, self).setUp()
        self.partner_obj = self.env['res.partner']
        self.product_obj = self.env['product.product']
        self.account_tax_obj = self.env['account.tax']
        self.account_obj = self.env['account.account']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_line_obj = self.env['account.invoice.line']
        self.voucher_obj = self.env['account.voucher']
        self.journal_obj = self.env['account.journal']
        self.payment_term_obj = self.env['account.payment.term']

        # Create partner
        partner_data = {
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'}
        self.partner_01 = self.partner_obj.create(partner_data)

        # Create products
        self.product_01 = self.product_obj.create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1',
            'list_price': 1.11})

        accounts_430 = self.account_obj.search([
            ('code', '=', '430000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not accounts_430.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'430000\' code.'))
        accounts_700 = self.account_obj.search([
            ('code', '=', '700000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not accounts_700.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'700000\' code.'))
        payment_terms = self.payment_term_obj.search([])
        if not payment_terms.exists():
            raise exceptions.Warning(_(
                'Does not exist any payment_term.'))

        self.taxs_21 = self.account_tax_obj.search([
            ('name', 'like', '%21%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_21.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'21\' in name.'))

        # Create customer invoice
        invoice_01_data = {
            'partner_id': self.partner_01.id,
            'date_due': fields.Date.today(),
            'currency_id': self.ref('base.EUR'),
            'reference_type': 'none',
            'company_id': self.ref('base.main_company'),
            'state': 'draft',
            'type': 'out_invoice',
            'account_id': accounts_430[0].id,
            'reconciled': 0,
            'date_invoice': fields.Date.today(),
            'amount_untaxed': 0,
            'amount_total': 0,
            'payment_term': payment_terms[0].id}
        self.invoice_01 = self.invoice_obj.create(invoice_01_data)

        # Create invoice lines
        invoice_line_01_data = {
            'invoice_id': self.invoice_01.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.product_01.product_tmpl_id.list_price,
            'price_subtotal': self.product_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.product_01.id,
            'quantity': 1,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'}
        self.invoice_line_01 = self.invoice_line_obj.create(
            invoice_line_01_data)
        invoice_line_02_data = {
            'invoice_id': self.invoice_01.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.product_01.product_tmpl_id.list_price,
            'price_subtotal': self.product_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.product_01.id,
            'quantity': 5,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'}
        self.invoice_line_02 = self.invoice_line_obj.create(
            invoice_line_02_data)

        # Validate invoice and check
        self.invoice_01.signal_workflow('invoice_open')
        self.assertEqual(self.invoice_01.state, 'open')

        # Create customer invoice refund
        invoice_02_data = {
            'partner_id': self.partner_01.id,
            'date_due': fields.Date.today(),
            'currency_id': self.ref('base.EUR'),
            'reference_type': 'none',
            'company_id': self.ref('base.main_company'),
            'state': 'draft',
            'type': 'out_refund',
            'account_id': accounts_430[0].id,
            'reconciled': 0,
            'date_invoice': fields.Date.today(),
            'amount_untaxed': 0,
            'amount_total': 0,
            'payment_term': payment_terms[0].id}
        self.invoice_02 = self.invoice_obj.create(invoice_02_data)

        # Create invoice lines
        invoice_line_01_data = {
            'invoice_id': self.invoice_02.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.product_01.product_tmpl_id.list_price,
            'price_subtotal': self.product_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.product_01.id,
            'quantity': 3,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'}
        self.invoice_line_01 = self.invoice_line_obj.create(
            invoice_line_01_data)
        invoice_line_02_data = {
            'invoice_id': self.invoice_02.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.product_01.product_tmpl_id.list_price,
            'price_subtotal': self.product_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.product_01.id,
            'quantity': 1,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'}
        self.invoice_line_02 = self.invoice_line_obj.create(
            invoice_line_02_data)

        # Validate invoice and check
        self.invoice_02.signal_workflow('invoice_open')
        self.assertEqual(self.invoice_02.state, 'open')

    def pay_invoice(self, invoice):
        '''Create payment for invoice passed as argument.'''
        # Register payment for invoice_01
        res = invoice.invoice_pay_customer()
        voucher_context = res['context']
        update = {}
        for dkey in voucher_context:
            if not dkey.startswith('default_'):
                continue
            key = re.sub(r'^default_', '', dkey)
            if voucher_context.get(key):
                continue
            update[key] = voucher_context[dkey]
        voucher_context.update(update)
        field_list = [
            'comment',
            'line_cr_ids',
            'is_multi_currency',
            'paid_amount_in_company_currency',
            'line_dr_ids',
            'journal_id',
            'currency_id',
            'narration',
            'partner_id',
            'payment_rate_currency_id',
            'reference',
            'writeoff_acc_id',
            'state',
            'pre_line',
            'type',
            'payment_option',
            'account_id',
            'company_id',
            'period_id',
            'date',
            'payment_rate',
            'name',
            'writeoff_amount',
            'analytic_id',
            'amount']
        voucher_values = self.voucher_obj.with_context(
            voucher_context).default_get(field_list)
        journals = self.journal_obj.search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not journals.exists():
            raise exceptions.Warning(_(
                'Does not exist any journal with \'cash\' type.'))
        res = self.voucher_obj.with_context(voucher_context).onchange_journal(
            journals[0].id,
            [],  # lines
            [],  # taxes
            voucher_values.get('partner_id'),
            voucher_values.get('date'),
            voucher_values.get('amount'),
            voucher_values.get('ttype'),
            voucher_values.get('company_id'))
        voucher_values.update(res['value'])
        voucher_values.update({'journal_id': journals[0].id})
        for key in ['line_dr_ids', 'line_cr_ids']:
            array = []
            for obj in voucher_values[key]:
                array.append([0, False, obj])
            voucher_values[key] = array
        voucher = self.voucher_obj.with_context(voucher_context).create(
            voucher_values)

        # Pay invoice and check
        voucher.with_context(voucher_context).button_proforma_voucher()
        self.assertEqual(invoice.state, 'paid')

    def test_without_paid(self):
        '''Without invoice lines paid associated.'''
        self.assertEqual(
            self.product_01.product_tmpl_id.sum_price, 0)

    def test_with_payment_invoice(self):
        '''With lines of invoices of type invoice with state invoice paid.'''
        self.pay_invoice(self.invoice_01)
        self.assertEqual(
            self.product_01.product_tmpl_id.sum_price, 6.66)

    def test_with_payment_invoice_refund(self):
        '''With lines of invoices of type refund with state invoice paid.'''
        self.pay_invoice(self.invoice_02)
        self.assertEqual(
            self.product_01.product_tmpl_id.sum_price, -4.44)

    def test_computed_count(self):
        '''Call compute methods.'''
        self.pay_invoice(self.invoice_01)
        self.pay_invoice(self.invoice_02)

        self.assertEqual(
            self.product_01.product_tmpl_id.sum_price, 2.22)
        self.assertEqual(
            self.product_01.product_tmpl_id.sum_price_cur_year,
            2.22)
        res = self.product_01.product_tmpl_id.action_view_invoices_cur_year()
        self.assertIn('domain', res)
        self.assertIn('res_model', res)
        lines = self.env[res['res_model']].search(res['domain'])
        self.assertEqual(len(lines), 4)

        # Modify date invoice 01 and check
        self.invoice_01.date_invoice = fields.Date.to_string(
            fields.Date.from_string(
                fields.Date.today()).replace(year=2000))
        self.product_01.product_tmpl_id._compute_product_invoiced()
        self.assertEqual(
            self.product_01.product_tmpl_id.sum_price, 2.22)
        self.assertEqual(
            self.product_01.product_tmpl_id.sum_price_cur_year, -4.44)

        # Call general button
        res = self.product_01.product_tmpl_id.action_view_invoices()
        self.assertIn('domain', res)
        self.assertIn('res_model', res)
        lines = self.env[res['res_model']].search(res['domain'])
        self.assertEqual(len(lines), 4)

        # Call current year button
        res = self.product_01.product_tmpl_id.action_view_invoices_cur_year()
        self.assertIn('domain', res)
        self.assertIn('res_model', res)
        lines = self.env[res['res_model']].search(res['domain'])
        self.assertEqual(len(lines), 2)
