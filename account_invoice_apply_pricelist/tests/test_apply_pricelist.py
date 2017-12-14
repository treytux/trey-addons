# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, exceptions


class TestApplyPricelist(common.TransactionCase):
    def setUp(self):
        super(TestApplyPricelist, self).setUp()
        self.tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1})
        self.pricelist_default_sale = self.env['product.pricelist'].create({
            'name': 'Default sale',
            'type': 'sale'})
        version_default_sale = self.env['product.pricelist.version'].create({
            'pricelist_id': self.pricelist_default_sale.id,
            'name': 'Default sale'})
        self.env['product.pricelist.item'].create({
            'price_version_id': version_default_sale.id,
            'name': 'Default sale',
            'sequence': 10,
            'base': self.ref('product.list_price')})
        self.pricelist_sale_disc = self.env['product.pricelist'].create({
            'name': '10% discount',
            'type': 'sale'})
        version_disc_sale = self.env['product.pricelist.version'].create({
            'pricelist_id': self.pricelist_sale_disc.id,
            'name': '10% discount version'})
        self.env['product.pricelist.item'].create({
            'price_version_id': version_disc_sale.id,
            'name': '10% discount item',
            'sequence': 10,
            'base': self.ref('product.list_price'),
            'price_discount': -0.1})
        self.pricelist_default_purchase = self.env[
            'product.pricelist'].create({
                'name': 'Default purchase',
                'type': 'purchase'})
        version_default_purchase = self.env[
            'product.pricelist.version'].create({
                'pricelist_id': self.pricelist_default_purchase.id,
                'name': 'Default purchase'})
        self.env['product.pricelist.item'].create({
            'price_version_id': version_default_purchase.id,
            'name': 'Default purchase',
            'sequence': 10,
            'base': self.ref('product.list_price')})
        self.pricelist_purchase_disc = self.env['product.pricelist'].create({
            'name': '20% discount',
            'type': 'purchase'})
        version_disc_purchase = self.env['product.pricelist.version'].create({
            'pricelist_id': self.pricelist_purchase_disc.id,
            'name': '20% discount version'})
        self.env['product.pricelist.item'].create({
            'price_version_id': version_disc_purchase.id,
            'name': '20% discount item',
            'sequence': 10,
            'base': self.ref('product.list_price'),
            'price_discount': -0.2})
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'property_product_pricelist': self.pricelist_default_sale.id,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})
        self.customer_02 = self.env['res.partner'].create({
            'name': 'Customer 02',
            'is_company': True,
            'customer': True,
            'property_product_pricelist': None,
            'email': 'customer2@test.com',
            'street': 'Calle Sol, 1',
            'phone': '666777777'})
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Supplier 01',
            'is_company': True,
            'supplier': True,
            'property_product_pricelist_purchase': (
                self.pricelist_default_purchase.id),
            'email': 'supplier1@test.com',
            'street': 'Plaza General, 2',
            'phone': '666888999'})
        self.supplier_02 = self.env['res.partner'].create({
            'name': 'Supplier 02',
            'is_company': True,
            'supplier': True,
            'property_product_pricelist_purchase': None,
            'email': 'supplier2@test.com',
            'street': 'Avda Libertad, 6',
            'phone': '666778877'})
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
            'taxes_id': [(6, 0, [self.tax_21.id])]})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': 10})
        self.inv_cust_01 = self.env['account.invoice'].create({
            'type': 'out_invoice',
            'partner_id': self.customer_01.id,
            'account_id': self.account.id,
            'date_invoice': fields.Date.today()})
        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.inv_cust_01.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})
        self.inv_cust_02 = self.env['account.invoice'].create({
            'type': 'out_invoice',
            'partner_id': self.customer_01.id,
            'account_id': self.account.id,
            'date_invoice': fields.Date.today()})
        self.invoice_line_02 = self.env['account.invoice.line'].create({
            'invoice_id': self.inv_cust_02.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 2})
        self.inv_cust_03 = self.env['account.invoice'].create({
            'type': 'out_invoice',
            'partner_id': self.customer_02.id,
            'account_id': self.account.id,
            'date_invoice': fields.Date.today()})
        self.invoice_line_03 = self.env['account.invoice.line'].create({
            'invoice_id': self.inv_cust_03.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})
        self.inv_suppl_02 = self.env['account.invoice'].create({
            'type': 'in_invoice',
            'partner_id': self.supplier_01.id,
            'account_id': self.account.id,
            'date_invoice': fields.Date.today()})
        self.invoice_line_02 = self.env['account.invoice.line'].create({
            'invoice_id': self.inv_suppl_02.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})
        self.inv_suppl_03 = self.env['account.invoice'].create({
            'type': 'in_invoice',
            'partner_id': self.supplier_02.id,
            'account_id': self.account.id,
            'date_invoice': fields.Date.today()})
        self.invoice_line_02 = self.env['account.invoice.line'].create({
            'invoice_id': self.inv_suppl_03.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})

    def test_invoice_apply_pricelist_customer_default(self):
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_cust_01.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_cust_01.id}).create({})
        wiz.action_accept()
        self.assertEqual(
            self.inv_cust_01.partner_id.property_product_pricelist.name,
            'Default sale')
        self.assertEqual(self.inv_cust_01.amount_untaxed, 10)
        self.assertEqual(self.inv_cust_01.amount_tax, 2.1)
        self.assertEqual(self.inv_cust_01.amount_total, 12.1)

    def test_invoice_apply_pricelist_customer_discount(self):
        self.customer_01.property_product_pricelist = (
            self.pricelist_sale_disc.id)
        self.assertEqual(
            self.customer_01.property_product_pricelist.name, '10% discount')
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_cust_01.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_cust_01.id}).create({})
        wiz.action_accept()
        self.assertEqual(self.inv_cust_01.amount_untaxed, 9)
        self.assertEqual(self.inv_cust_01.amount_tax, 1.89)
        self.assertEqual(self.inv_cust_01.amount_total, 10.89)

    def test_invoice_apply_pricelist_customer_without_pricelist(self):
        self.assertFalse(self.customer_02.property_product_pricelist)
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_cust_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_cust_03.id}).create({})
        self.assertRaises(Exception, wiz.action_accept)

    def test_invoice_apply_pricelist_customer_no_draft(self):
        self.inv_cust_03.signal_workflow('invoice_cancel')
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_cust_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_cust_03.id}).create({})
        self.assertRaises(Exception, wiz.action_accept)

    def test_invoices_apply_pricelist_customer_no_draft(self):
        self.inv_cust_01.signal_workflow('invoice_cancel')
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': [self.inv_cust_01.ids[0], self.inv_cust_02.ids[0]],
            'active_model': 'account.invoice',
            'active_id': self.inv_cust_01.id}).create({})
        self.assertRaises(Exception, wiz.action_accept)

    def test_invoices_apply_pricelist_customer_default(self):
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': [self.inv_cust_01.ids[0], self.inv_cust_02.ids[0]],
            'active_model': 'account.invoice',
            'active_id': self.inv_cust_01.id}).create({})
        wiz.action_accept()
        self.assertEqual(
            self.inv_cust_01.partner_id.property_product_pricelist.name,
            'Default sale')
        self.assertEqual(
            self.inv_cust_02.partner_id.property_product_pricelist.name,
            'Default sale')
        self.assertEqual(self.inv_cust_01.amount_untaxed, 10)
        self.assertEqual(self.inv_cust_01.amount_tax, 2.1)
        self.assertEqual(self.inv_cust_01.amount_total, 12.1)
        self.assertEqual(self.inv_cust_02.amount_untaxed, 20)
        self.assertEqual(self.inv_cust_02.amount_tax, 4.2)
        self.assertEqual(self.inv_cust_02.amount_total, 24.2)

    def test_invoice_apply_pricelist_supplier_default(self):
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_suppl_02.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_suppl_02.id}).create({})
        wiz.action_accept()
        pricelist = (
            self.inv_suppl_02.partner_id.property_product_pricelist_purchase)
        self.assertEqual(pricelist.name, 'Default purchase')
        self.assertEqual(self.inv_suppl_02.amount_untaxed, 10)
        self.assertEqual(self.inv_suppl_02.amount_tax, 2.1)
        self.assertEqual(self.inv_suppl_02.amount_total, 12.1)

    def test_invoice_apply_pricelist_supplier_discount(self):
        self.supplier_01.property_product_pricelist_purchase = (
            self.pricelist_purchase_disc.id)
        self.assertEqual(
            self.supplier_01.property_product_pricelist_purchase.name,
            '20% discount')
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_suppl_02.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_suppl_02.id}).create({})
        wiz.action_accept()
        self.assertEqual(self.inv_suppl_02.amount_untaxed, 8)
        self.assertEqual(self.inv_suppl_02.amount_tax, 1.68)
        self.assertEqual(self.inv_suppl_02.amount_total, 9.68)

    def test_invoice_apply_pricelist_supplier_without_pricelist(self):
        self.assertFalse(self.supplier_02.property_product_pricelist_purchase)
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_suppl_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_suppl_03.id}).create({})
        self.assertRaises(Exception, wiz.action_accept)

    def test_invoice_apply_pricelist_supplier_no_draft(self):
        self.inv_suppl_03.signal_workflow('invoice_cancel')
        wiz = self.env['wizard.invoice_apply_pricelist'].with_context({
            'active_ids': self.inv_suppl_03.ids,
            'active_model': 'account.invoice',
            'active_id': self.inv_suppl_03.id}).create({})
        self.assertRaises(Exception, wiz.action_accept)
