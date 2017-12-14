# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase
from openerp import fields, _, exceptions
import logging
_log = logging.getLogger(__name__)


class InvoiceTaxAccountCase(TransactionCase):

    def setUp(self):
        super(InvoiceTaxAccountCase, self).setUp()
        self.taxs_21 = self.env['account.tax'].search([
            ('name', '=', 'IVA 21%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_21.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'21\' in name.'))
        self.tax_21 = self.taxs_21[0]
        self.taxs_4 = self.env['account.tax'].search([
            ('name', '=', 'IVA 4%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_4.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'4\' in name.'))
        self.tax_4 = self.taxs_4[0]
        self.taxs_10 = self.env['account.tax'].search([
            ('name', '=', 'IVA 10%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_10.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'10\' in name.'))
        self.tax_10 = self.taxs_10[0]
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
        accounts_700 = self.env['account.account'].search([
            ('code', '=', '700000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not accounts_700.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'700000\' code.'))
        payment_terms = self.env['account.payment.term'].search([])
        if not payment_terms.exists():
            raise exceptions.Warning(_('Does not exist any payment_term.'))
        self.invoice_01 = self.env['account.invoice'].create({
            'partner_id': self.partner_01.id,
            'date_due': fields.Date.today(),
            'currency_id': self.ref('base.EUR'),
            'reference_type': 'none',
            'company_id': self.ref('base.main_company'),
            'state': 'draft',
            'type': 'out_invoice',
            'account_id': accounts_430[0].id,
            'date_invoice': fields.Date.today(),
            'payment_term': payment_terms[0].id})
        self.invoice_line_1_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'price_subtotal': self.pp_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'product_id': self.pp_01.id,
            'quantity': 1,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'})
        self.invoice_line_1_2 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'price_subtotal': self.pp_02.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'product_id': self.pp_02.id,
            'quantity': 3,
            'partner_id': self.partner_01.id,
            'name': 'Test 2'})
        self.invoice_02 = self.env['account.invoice'].create({
            'partner_id': self.partner_01.id,
            'date_due': fields.Date.today(),
            'currency_id': self.ref('base.EUR'),
            'reference_type': 'none',
            'company_id': self.ref('base.main_company'),
            'state': 'draft',
            'type': 'out_invoice',
            'account_id': accounts_430[0].id,
            'date_invoice': fields.Date.today(),
            'payment_term': payment_terms[0].id})
        self.invoice_line_2_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_02.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'price_subtotal': self.pp_01.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'product_id': self.pp_01.id,
            'quantity': 2,
            'partner_id': self.partner_01.id,
            'name': 'Test 1'})
        self.invoice_line_2_2 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_02.id,
            'account_id': accounts_700[0].id,
            'uos_id': self.ref('product.product_uom_unit'),
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'price_subtotal': self.pp_02.product_tmpl_id.list_price,
            'company_id': self.ref('base.main_company'),
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'product_id': self.pp_02.id,
            'quantity': 4,
            'partner_id': self.partner_01.id,
            'name': 'Test 2'})

    def test_account_invoice_tax_change_01(self):
        '''Select one invoice and assign one tax.'''
        self.assertEqual(
            self.invoice_line_1_1.invoice_line_tax_id, self.tax_21)
        self.assertEqual(
            self.invoice_line_1_2.invoice_line_tax_id, self.tax_21)
        self.invoice_01.button_reset_taxes()
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 14.70)
        self.assertEqual(self.invoice_01.amount_total, 84.70)
        wiz = self.env['wiz.invoice.tax.change'].with_context({
            'active_ids': [self.invoice_01.id],
            'active_model': 'account.invoice',
            'active_id': self.invoice_01.id}).create({
                'tax_ids': [(6, 0, [self.tax_4.id])]})
        wiz.button_accept()
        self.assertEqual(self.invoice_line_1_1.invoice_line_tax_id, self.tax_4)
        self.assertEqual(self.invoice_line_1_2.invoice_line_tax_id, self.tax_4)
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 2.80)
        self.assertEqual(self.invoice_01.amount_total, 72.80)

    def test_account_invoice_tax_change_02(self):
        '''Select one invoice and assign several taxs.'''
        self.assertEqual(
            self.invoice_line_1_1.invoice_line_tax_id, self.tax_21)
        self.assertEqual(
            self.invoice_line_1_2.invoice_line_tax_id, self.tax_21)
        self.invoice_01.button_reset_taxes()
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 14.70)
        self.assertEqual(self.invoice_01.amount_total, 84.70)
        wiz = self.env['wiz.invoice.tax.change'].with_context({
            'active_ids': [self.invoice_01.id],
            'active_model': 'account.invoice',
            'active_id': self.invoice_01.id}).create({
                'tax_ids': [(6, 0, [self.tax_4.id, self.tax_10.id])]})
        wiz.button_accept()
        self.assertIn(self.tax_4, self.invoice_line_1_1.invoice_line_tax_id)
        self.assertIn(self.tax_10, self.invoice_line_1_1.invoice_line_tax_id)
        self.assertIn(self.tax_4, self.invoice_line_1_2.invoice_line_tax_id)
        self.assertIn(self.tax_10, self.invoice_line_1_2.invoice_line_tax_id)
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 9.80)
        self.assertEqual(self.invoice_01.amount_total, 79.80)

    def test_account_invoice_tax_change_03(self):
        '''Select several invoices and assign one tax.'''
        self.assertEqual(
            self.invoice_line_1_1.invoice_line_tax_id, self.tax_21)
        self.assertEqual(
            self.invoice_line_1_2.invoice_line_tax_id, self.tax_21)
        self.invoice_01.button_reset_taxes()
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 14.70)
        self.assertEqual(self.invoice_01.amount_total, 84.70)
        self.assertEqual(
            self.invoice_line_2_1.invoice_line_tax_id, self.tax_21)
        self.assertEqual(
            self.invoice_line_2_2.invoice_line_tax_id, self.tax_21)
        self.invoice_02.button_reset_taxes()
        self.assertEqual(self.invoice_02.amount_untaxed, 100)
        self.assertEqual(self.invoice_02.amount_tax, 21)
        self.assertEqual(self.invoice_02.amount_total, 121)
        wiz = self.env['wiz.invoice.tax.change'].with_context({
            'active_ids': [self.invoice_01.id, self.invoice_02.id],
            'active_model': 'account.invoice'}).create({
                'tax_ids': [(6, 0, [self.tax_4.id])]})
        wiz.button_accept()
        self.assertEqual(self.invoice_line_1_1.invoice_line_tax_id, self.tax_4)
        self.assertEqual(self.invoice_line_1_2.invoice_line_tax_id, self.tax_4)
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 2.80)
        self.assertEqual(self.invoice_01.amount_total, 72.80)
        self.assertEqual(self.invoice_line_2_1.invoice_line_tax_id, self.tax_4)
        self.assertEqual(self.invoice_line_2_2.invoice_line_tax_id, self.tax_4)
        self.assertEqual(self.invoice_02.amount_untaxed, 100)
        self.assertEqual(self.invoice_02.amount_tax, 4)
        self.assertEqual(self.invoice_02.amount_total, 104)

    def test_account_invoice_tax_change_04(self):
        '''Select several invoices and assign several taxs.'''
        self.assertEqual(
            self.invoice_line_1_1.invoice_line_tax_id, self.tax_21)
        self.assertEqual(
            self.invoice_line_1_2.invoice_line_tax_id, self.tax_21)
        self.invoice_01.button_reset_taxes()
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 14.70)
        self.assertEqual(self.invoice_01.amount_total, 84.70)
        self.assertEqual(
            self.invoice_line_2_1.invoice_line_tax_id, self.tax_21)
        self.assertEqual(
            self.invoice_line_2_2.invoice_line_tax_id, self.tax_21)
        self.invoice_02.button_reset_taxes()
        self.assertEqual(self.invoice_02.amount_untaxed, 100)
        self.assertEqual(self.invoice_02.amount_tax, 21)
        self.assertEqual(self.invoice_02.amount_total, 121)
        wiz = self.env['wiz.invoice.tax.change'].with_context({
            'active_ids': [self.invoice_01.id, self.invoice_02.id],
            'active_model': 'account.invoice'}).create({
                'tax_ids': [(6, 0, [self.tax_4.id, self.tax_10.id])]})
        wiz.button_accept()
        self.assertIn(self.tax_4, self.invoice_line_1_1.invoice_line_tax_id)
        self.assertIn(self.tax_10, self.invoice_line_1_1.invoice_line_tax_id)
        self.assertIn(self.tax_4, self.invoice_line_1_2.invoice_line_tax_id)
        self.assertIn(self.tax_10, self.invoice_line_1_2.invoice_line_tax_id)
        self.assertEqual(self.invoice_01.amount_untaxed, 70)
        self.assertEqual(self.invoice_01.amount_tax, 9.80)
        self.assertEqual(self.invoice_01.amount_total, 79.80)

        self.assertIn(self.tax_4, self.invoice_line_2_1.invoice_line_tax_id)
        self.assertIn(self.tax_10, self.invoice_line_2_1.invoice_line_tax_id)
        self.assertIn(self.tax_4, self.invoice_line_2_2.invoice_line_tax_id)
        self.assertIn(self.tax_10, self.invoice_line_2_2.invoice_line_tax_id)
        self.assertEqual(self.invoice_02.amount_untaxed, 100)
        self.assertEqual(self.invoice_02.amount_tax, 14)
        self.assertEqual(self.invoice_02.amount_total, 114)
