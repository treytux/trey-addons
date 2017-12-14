# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, exceptions
import logging
_log = logging.getLogger(__name__)


class TestInvoiceDiscount(common.TransactionCase):
    def setUp(self):
        super(TestInvoiceDiscount, self).setUp()
        self.taxs_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company')})
        if not self.taxs_21.exists():
            raise exceptions.Warning(
                'Does not exist any account tax with \'21\' in name.')
        self.taxs_10 = self.env['account.tax'].create({
            'name': '%10%',
            'type': 'percent',
            'amount': 0.1,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company')})
        if not self.taxs_10.exists():
            raise exceptions.Warning(
                'Does not exist any account tax with \'10\' in name.')
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})
        user_types = self.env['account.account.type'].search([])
        if not user_types:
            raise exceptions.Warning('Does not exist any account account type')
        self.user_type = user_types[0]
        self.account = self.env['account.account'].create({
            'name': 'Account for test module',
            'type': 'other',
            'user_type': self.user_type.id,
            'code': '11111',
            'currency_mode': 'current',
            'company_id': self.ref('base.main_company')})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.taxs_21.id])]})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': 10})
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'consu'})
        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id,
            'list_price': 10})
        self.pt_03 = self.env['product.template'].create({
            'name': 'Discount product',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.taxs_21.id])]})
        self.pp_03 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_03.id,
            'list_price': 33})
        self.invoice_01 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'date_invoice': fields.Date.today(),
            'partner_id': self.partner_01.id})
        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})
        self.invoice_02 = self.env['account.invoice'].create({
            'partner_id': self.partner_01.id,
            'date_invoice': fields.Date.today(),
            'account_id': self.account.id})
        self.invoice_line_02 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_02.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})
        self.invoice_03 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'date_invoice': fields.Date.today(),
            'partner_id': self.partner_01.id})
        self.invoice_line_03 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_03.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21[0].id])],
            'name': self.pp_03.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})

    def test_invoice_discount_percent_line(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_01.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_01.id}).create({
                'discount_type': 'percent_line',
                'discount_applied': 10.0})
        wiz.button_accept()
        self.invoice_01.button_reset_taxes()
        self.assertEqual(self.invoice_line_01.discount, 10)
        self.assertEqual(self.invoice_line_01.price_subtotal, 9)
        self.assertEqual(self.invoice_01.amount_untaxed, 9)
        self.assertEqual(self.invoice_01.amount_tax, 1.89)
        self.assertEqual(self.invoice_01.amount_total, 10.89)

    def test_invoice_discount_percent_total_error(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_02.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 333.0})
        wiz.product_id = wiz.onchange_product_id()
        self.assertRaises(Exception, wiz.button_accept)

    def test_invoice_discount_percent_total_product_without_taxs(self):

        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_02.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 10.0})
        wiz.product_id = wiz.onchange_product_id()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_tax_ids, self.pp_02.product_tmpl_id.taxes_id)
        self.invoice_02.button_reset_taxes()
        self.assertEqual(self.invoice_02.invoice_line[0].price_subtotal, 10)
        self.assertEqual(self.invoice_02.invoice_line[1].price_subtotal, -1)
        self.assertEqual(self.invoice_02.amount_untaxed, 9)
        self.assertEqual(self.invoice_02.amount_tax, 2.1)
        self.assertEqual(self.invoice_02.amount_total, 11.1)

    def test_invoice_discount_percent_total_product_with_taxs(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_02.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_03.id,
                'discount_applied': 10.0})
        wiz.product_id = wiz.onchange_product_id()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_tax_ids, self.pp_03.product_tmpl_id.taxes_id)
        self.invoice_02.button_reset_taxes()
        self.assertEqual(self.invoice_02.invoice_line[0].price_subtotal, 10)
        self.assertEqual(self.invoice_02.invoice_line[1].price_subtotal, -1)
        self.assertEqual(self.invoice_02.amount_untaxed, 9)
        self.assertEqual(self.invoice_02.amount_tax, 1.89)
        self.assertEqual(self.invoice_02.amount_total, 10.89)

    def test_invoice_discount_percent_total_with_discount_tax(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_02.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 10.0,
                'discount_tax_ids': [(6, 0, [self.taxs_10.id])]})
        wiz.button_accept()
        self.assertEqual(wiz.discount_tax_ids, self.taxs_10)
        self.invoice_02.button_reset_taxes()
        self.assertEqual(self.invoice_02.invoice_line[0].price_subtotal, 10)
        self.assertEqual(self.invoice_02.invoice_line[1].price_subtotal, -1)
        self.assertEqual(self.invoice_02.amount_untaxed, 9)
        self.assertEqual(self.invoice_02.amount_tax, 2)
        self.assertEqual(self.invoice_02.amount_total, 11)

    def test_invoice_discount_percent_total_with_discount_taxs(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_02.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 10.0,
                'discount_tax_ids': [
                    (6, 0, [self.taxs_10.id, self.taxs_21.id])]})
        wiz.button_accept()
        self.assertIn(self.taxs_10, wiz.discount_tax_ids)
        self.assertIn(self.taxs_21, wiz.discount_tax_ids)
        self.invoice_02.button_reset_taxes()
        self.assertEqual(self.invoice_02.invoice_line[0].price_subtotal, 10)
        self.assertEqual(self.invoice_02.invoice_line[1].price_subtotal, -1)
        self.assertEqual(self.invoice_02.amount_untaxed, 9)
        self.assertEqual(self.invoice_02.amount_tax, 1.79)
        self.assertEqual(self.invoice_02.amount_total, 10.79)

    def test_invoice_discount_quantity_total_product_without_taxs(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_03.id}).create({
                'discount_type': 'quantity_total',
                'discount_quantity': 1,
                'product_id': self.pp_02.id})
        wiz.product_id = wiz.onchange_product_id()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_tax_ids, self.pp_02.product_tmpl_id.taxes_id)
        self.invoice_03.button_reset_taxes()
        self.assertEqual(self.invoice_03.amount_untaxed, 9)
        self.assertEqual(self.invoice_03.amount_tax, 2.1)
        self.assertEqual(self.invoice_03.amount_total, 11.1)

    def test_invoice_discount_quantity_total_product_with_taxs(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_03.id}).create({
                'discount_type': 'quantity_total',
                'discount_quantity': 1.0,
                'product_id': self.pp_02.id})
        wiz.button_accept()
        wiz.product_id = wiz.onchange_product_id()
        self.invoice_03.button_reset_taxes()
        self.assertEqual(self.invoice_03.amount_untaxed, 9)
        self.assertEqual(self.invoice_03.amount_tax, 2.1)
        self.assertEqual(self.invoice_03.amount_total, 11.1)

    def test_invoice_discount_quantity_total_with_discount_tax(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_03.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_02.id,
                'discount_quantity': 1,
                'discount_tax_ids': [(6, 0, [self.taxs_10.id])]})
        wiz.button_accept()
        self.assertEqual(wiz.discount_tax_ids, self.taxs_10)
        self.invoice_03.button_reset_taxes()
        self.assertEqual(self.invoice_03.invoice_line[0].price_subtotal, 10)
        self.assertEqual(self.invoice_03.invoice_line[1].price_subtotal, -1)
        self.assertEqual(self.invoice_03.amount_untaxed, 9)
        self.assertEqual(self.invoice_03.amount_tax, 2)
        self.assertEqual(self.invoice_03.amount_total, 11)

    def test_invoice_discount_quantity_total_with_discount_taxs(self):
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_03.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_02.id,
                'discount_quantity': 1,
                'discount_tax_ids': [
                    (6, 0, [self.taxs_10.id, self.taxs_21.id])]})
        wiz.button_accept()
        self.assertIn(self.taxs_10, wiz.discount_tax_ids)
        self.assertIn(self.taxs_21, wiz.discount_tax_ids)
        self.invoice_03.button_reset_taxes()
        self.assertEqual(self.invoice_03.invoice_line[0].price_subtotal, 10)
        self.assertEqual(self.invoice_03.invoice_line[1].price_subtotal, -1)
        self.assertEqual(self.invoice_03.amount_untaxed, 9)
        self.assertEqual(self.invoice_03.amount_tax, 1.79)
        self.assertEqual(self.invoice_03.amount_total, 10.79)

    def test_invoice_discount_quantity_total_with_discount_taxs_no_draft(self):
        self.invoice_03.signal_workflow('invoice_cancel')
        wiz = self.env['wiz.invoice.discount'].with_context({
            'active_ids': self.invoice_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.invoice_03.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_02.id,
                'discount_quantity': 1,
                'discount_tax_ids': [
                    (6, 0, [self.taxs_10.id, self.taxs_21.id])]})
        self.assertRaises(Exception, wiz.button_accept)
