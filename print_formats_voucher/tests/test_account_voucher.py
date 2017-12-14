# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, tools, exceptions, _
import os
import re
import logging
_log = logging.getLogger(__name__)


class TestAccountVoucher(common.TransactionCase):

    def setUp(self):
        super(TestAccountVoucher, self).setUp()
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'default_code': '123456'})
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'consu'})
        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id,
            'default_code': '123456'})

        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})

        self.taxs_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company')})
        if not self.taxs_21.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'21\' in name.'))

        accounts_430 = self.env['account.account'].search([
            ('code', '=', '430000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not accounts_430.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'430000\' code.'))
        accounts_700 = self.env['account.account'].search([
            ('code', '=', '700000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not accounts_700.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'700000\' code.'))
        payment_terms = self.env['account.payment.term'].search([])
        if not payment_terms.exists():
            raise exceptions.Warning(_(
                'Does not exist any payment_term.'))

        self.invoice_01 = self.env['account.invoice'].create({
            'account_id': accounts_430[0].id,
            'reference_type': 'none',
            'partner_id': self.partner_01.id,
            'journal_id': self.ref('account.sales_journal'),
            'date_due': fields.Date.today(),
            'currency_id': self.ref('base.EUR'),
            'company_id': self.ref('base.main_company'),
            'state': 'draft',
            'type': 'out_invoice',
            'reconciled': 0,
            'date_invoice': fields.Date.today(),
            'amount_untaxed': 0,
            'amount_total': 0,
            'payment_term': payment_terms[0].id})

        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'price_subtotal': self.pp_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.pp_01.id,
            'quantity': 1,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'})
        self.invoice_line_02 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'price_subtotal': self.pp_02.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.pp_02.id,
            'quantity': 3,
            'partner_id': self.partner_01.id,
            'name': 'Test 2'})

        self.invoice_01.signal_workflow('invoice_open')
        self.assertEqual(self.invoice_01.state, 'open')

        res = self.invoice_01.invoice_pay_customer()
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
        voucher_values = self.env['account.voucher'].with_context(
            voucher_context).default_get(field_list)
        journals = self.env['account.journal'].search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not journals.exists():
            raise exceptions.Warning(_(
                'Does not exist any journal with \'cash\' type.'))
        res = self.env['account.voucher'].with_context(
            voucher_context).onchange_journal(
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
        self.voucher = self.env['account.voucher'].with_context(
            voucher_context).create(voucher_values)
        self.voucher.with_context(voucher_context).button_proforma_voucher()

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_account_voucher_report(self):
        self.assertEqual(self.invoice_01.state, 'paid')
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_print_formats_voucher.pdf')
        self.print_report(
            self.voucher, 'print_formats_voucher.report_account_voucher',
            instance_path)
