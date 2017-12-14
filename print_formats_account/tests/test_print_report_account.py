# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, tools, exceptions, _
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintReportAccount(common.TransactionCase):

    def setUp(self):
        super(TestPrintReportAccount, self).setUp()
        self.payment_term_line_obj = self.env['account.payment.term.line']
        self.payment_term = self.env['account.payment.term'].create({
            'name': '30% adelantado y despues 30 dias',
            'note': 'Explication'})
        self.payment_term_line_01 = self.payment_term_line_obj.create({
            'payment_id': self.payment_term.id,
            'value': 'procent',
            'value_amount': 0.5,
            'days': '0',
            'days2': '0'})
        self.payment_term_line_02 = self.payment_term_line_obj.create({
            'payment_id': self.payment_term.id,
            'value': 'balance',
            'value_amount': 0.5,
            'days': '30',
            'days2': '-1'})

        self.payment_mode_type = self.env['payment.mode.type'].create({
            'name': 'ManualBank',
            'code': 'OURSBANK'})
        self.user_type = self.env['account.account.type'].create({
            'name': 'A cobrar',
            'code': 'receivable',
            'report_type': 'asset',
            'close_method': 'unreconciled'})
        self.accounts_430 = self.env['account.account'].search([
            ('code', '=', '430000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.accounts_430.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'430000\' code.'))
        self.accounts_700 = self.env['account.account'].search([
            ('code', '=', '700000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.accounts_700.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'700000\' code.'))

        self.res_bank = self.env['res.bank'].create({
            'name': 'test bank',
            'bic': 'FTNOFRP1XXX'})

        self.partner_bank_01 = self.env['res.partner.bank'].create({
            'bank_name': 'MyBank',
            'state': 'iban',
            'acc_number': 'FR76 4242 4242 4242 4242 4242 424'})

        self.account_journal = self.env['account.journal'].create({
            'code': 'JJJI',
            'name': 'bank journal',
            'type': 'sale',
            'default_debit_account_id': self.accounts_430.id,
            'default_credit_account_id': self.accounts_430.id,
            'sequence_id': self.ref(
                'account.sequence_refund_purchase_journal')})

        self.payment_mode_01 = self.env['payment.mode'].create({
            'name': 'MoneyBank',
            'bank_id': self.partner_bank_01.id,
            'type': self.payment_mode_type.id,
            'journal': self.account_journal.id,
            'company_id': self.ref('base.main_company')})

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

        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})

        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'default_code': '123456'})

        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'product'})

        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id,
            'default_code': '123456',
            'uom_id': self.ref('product.product_uom_unit')})

        self.invoice_01 = self.env['account.invoice'].create({
            'partner_id': self.partner_01.id,
            'account_id': self.accounts_430.id,
            'origin': 'SO004',
            'state': 'proforma2',
            'name': 'Reference',
            'journal_id': self.account_journal.id,
            'date_invoice': fields.Date.today(),
            'comment': 'Lorem ipsum dolor sit amet, consectetur adipisicing '
                       'elit, sed do eiusmod tempor incididunt ut labore et '
                       'dolore magna aliqua. Ut enim ad minim veniam, quis '
                       'nostrud exercitation ullamco laboris nisi ut aliquip '
                       'ex ea commodo consequat. Duis aute irure dolor in '
                       'reprehenderit in voluptate velit essecillum dolore '
                       'eu fugiat nulla pariatur. Excepteur sint occaecat '
                       'cupidatat non proident, sunt in culpa qui officia '
                       'deserunt mollit anim id est laborum.',
            'payment_mode_id': self.payment_mode_01.id,
            'partner_bank_id': self.partner_bank_01.id,
            'payment_term': self.env.ref(
                'account.account_payment_term_line_net').id})

        # Create invoice lines
        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'account_id': self.partner_01.property_account_receivable.id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.pp_01.id,
            'quantity': 10,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'})
        self.invoice_01.button_compute()

        # Validate invoice and check
        self.invoice_01.signal_workflow('invoice_open')
        self.assertEqual(self.invoice_01.state, 'open')

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_invoice_report(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_print_formats_account_invoice.pdf')
        self.print_report(
            self.invoice_01, 'account.report_invoice',
            instance_path)
