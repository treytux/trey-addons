# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, exceptions, _
import re
import logging
_log = logging.getLogger(__name__)


class TestDummyData(common.TransactionCase):
    def setUp(self):
        super(TestDummyData, self).setUp()
        self.webservice = self.env['booking.webservice']
        self.bw_methabook_booking = self.env.ref(
            'booking_webservice_methabook.bw_methabook_booking')
        self.account = self.env['account.account'].search(
            [('type', '=', 'receivable'),
             ('currency_id', '=', False)], limit=1)[0]
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
            'name': 'ManualBankPower',
            'code': 'OURSBANKPW'})
        self.user_type = self.env['account.account.type'].create({
            'name': 'A cobrar',
            'code': 'receivable',
            'report_type': 'asset',
            'close_method': 'unreconciled'})

        self.account_430 = self.env['account.account'].create({
            'name': 'Account for test module',
            'type': 'other',
            'user_type': self.user_type.id,
            'code': 430000,
            'currency_mode': 'current',
            'company_id': self.env.user.company_id.id})

        if not self.account_430.exists():
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
            'default_debit_account_id': self.account_430.id,
            'default_credit_account_id': self.account_430.id,
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

        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1',
            'list_price': 11.11,
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'default_code': '123456'})

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
        self.voucher_obj = self.env['account.voucher']
        voucher_values = self.voucher_obj.with_context(
            voucher_context).default_get(field_list)
        self.journal_obj = self.env['account.journal']
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

        voucher.sudo().with_context(voucher_context).button_proforma_voucher()
        # self.assertEqual(invoice.state, 'paid')

    def create_and_pay_my_invoice(self, customer):
        self.invoice_01 = self.env['account.invoice'].create({
            'partner_id': customer.id,
            'account_id': self.account_430.id,
            # 'origin': 'SO004',
            'state': 'proforma2',
            # 'state': 'draft',
            'type': 'out_invoice',
            'name': 'Reference',
            'journal_id': self.account_journal.id,
            # 'date_invoice': fields.Date.to_string(inv_date),
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
            'currency_id': self.ref('base.EUR'),
            'date_due': fields.Date.today(),
            'reference_type': 'none',
            'company_id': self.ref('base.main_company'),
            'reconciled': 0,
            'payment_term': self.env.ref(
                'account.account_payment_term_line_net').id})

        # Create invoice lines
        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'account_id': customer.property_account_receivable.id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'product_id': self.pp_01.id,
            'quantity': 10,
            'partner_id': customer.id,
            'name': 'Test 1'})
        self.invoice_01.button_compute()

        # Validate invoice and check
        self.invoice_01.signal_workflow('invoice_open')
        # self.assertEqual(self.invoice_01.state, 'paid')

        # Pay invoice and check
        self.pay_invoice(self.invoice_01)
        self.assertEqual(self.invoice_01.state, 'paid')
        # self.assertEqual(
        #     self.product_01.product_tmpl_id.sum_price, 6.66)
        return True
