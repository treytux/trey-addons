# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase
from openerp import fields, _, exceptions


class SaleOrderTaxAccountCase(TransactionCase):

    def setUp(self):
        super(SaleOrderTaxAccountCase, self).setUp()
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
        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.order_line_1_1 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [self.tax_21.id])]})
        self.order_line_1_2 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'product_id': self.pp_02.id,
            'product_uom_qty': 3,
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [self.tax_21.id])]})
        self.order_02 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.order_line_2_1 = self.env['sale.order.line'].create({
            'order_id': self.order_02.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 2,
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [self.tax_21.id])]})
        self.order_line_2_2 = self.env['sale.order.line'].create({
            'order_id': self.order_02.id,
            'product_id': self.pp_02.id,
            'product_uom_qty': 4,
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [self.tax_21.id])]})

    def test_sale_order_tax_change_01(self):
        '''Select one sale order and assign one tax.'''
        self.assertEqual(self.order_line_1_1.tax_id, self.tax_21)
        self.assertEqual(self.order_line_1_2.tax_id, self.tax_21)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 14.70)
        self.assertEqual(self.order_01.amount_total, 84.70)
        wiz = self.env['wiz.sale.order.tax.change'].with_context({
            'active_ids': [self.order_01.id],
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'tax_ids': [(6, 0, [self.tax_4.id])]})
        wiz.button_accept()
        self.assertEqual(self.order_line_1_1.tax_id, self.tax_4)
        self.assertEqual(self.order_line_1_2.tax_id, self.tax_4)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 2.80)
        self.assertEqual(self.order_01.amount_total, 72.80)

    def test_sale_order_tax_change_02(self):
        '''Select one sale order and assign several taxs.'''
        self.assertEqual(self.order_line_1_1.tax_id, self.tax_21)
        self.assertEqual(self.order_line_1_2.tax_id, self.tax_21)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 14.70)
        self.assertEqual(self.order_01.amount_total, 84.70)
        wiz = self.env['wiz.sale.order.tax.change'].with_context({
            'active_ids': [self.order_01.id],
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'tax_ids': [(6, 0, [self.tax_4.id, self.tax_10.id])]})
        wiz.button_accept()
        self.assertIn(self.tax_4, self.order_line_1_1.tax_id)
        self.assertIn(self.tax_10, self.order_line_1_1.tax_id)
        self.assertIn(self.tax_4, self.order_line_1_2.tax_id)
        self.assertIn(self.tax_10, self.order_line_1_2.tax_id)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 9.80)
        self.assertEqual(self.order_01.amount_total, 79.80)

    def test_sale_order_tax_change_03(self):
        '''Select several sale orders and assign one tax.'''
        self.assertEqual(self.order_line_1_1.tax_id, self.tax_21)
        self.assertEqual(self.order_line_1_2.tax_id, self.tax_21)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 14.70)
        self.assertEqual(self.order_01.amount_total, 84.70)
        self.assertEqual(self.order_line_2_1.tax_id, self.tax_21)
        self.assertEqual(self.order_line_2_2.tax_id, self.tax_21)
        self.assertEqual(self.order_02.amount_untaxed, 100)
        self.assertEqual(self.order_02.amount_tax, 21)
        self.assertEqual(self.order_02.amount_total, 121)
        wiz = self.env['wiz.sale.order.tax.change'].with_context({
            'active_ids': [self.order_01.id, self.order_02.id],
            'active_model': 'sale.order'}).create({
                'tax_ids': [(6, 0, [self.tax_4.id])]})
        wiz.button_accept()
        self.assertEqual(self.order_line_1_1.tax_id, self.tax_4)
        self.assertEqual(self.order_line_1_2.tax_id, self.tax_4)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 2.80)
        self.assertEqual(self.order_01.amount_total, 72.80)
        self.assertEqual(self.order_line_2_1.tax_id, self.tax_4)
        self.assertEqual(self.order_line_2_2.tax_id, self.tax_4)
        self.assertEqual(self.order_02.amount_untaxed, 100)
        self.assertEqual(self.order_02.amount_tax, 4)
        self.assertEqual(self.order_02.amount_total, 104)

    def test_sale_order_tax_change_04(self):
        '''Select several sale orders and assign several taxs.'''
        self.assertEqual(self.order_line_1_1.tax_id, self.tax_21)
        self.assertEqual(self.order_line_1_2.tax_id, self.tax_21)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 14.70)
        self.assertEqual(self.order_01.amount_total, 84.70)
        self.assertEqual(self.order_line_2_1.tax_id, self.tax_21)
        self.assertEqual(self.order_line_2_2.tax_id, self.tax_21)
        self.assertEqual(self.order_02.amount_untaxed, 100)
        self.assertEqual(self.order_02.amount_tax, 21)
        self.assertEqual(self.order_02.amount_total, 121)
        wiz = self.env['wiz.sale.order.tax.change'].with_context({
            'active_ids': [self.order_01.id, self.order_02.id],
            'active_model': 'sale.order'}).create({
                'tax_ids': [(6, 0, [self.tax_4.id, self.tax_10.id])]})
        wiz.button_accept()
        self.assertIn(self.tax_4, self.order_line_1_1.tax_id)
        self.assertIn(self.tax_10, self.order_line_1_1.tax_id)
        self.assertIn(self.tax_4, self.order_line_1_2.tax_id)
        self.assertIn(self.tax_10, self.order_line_1_2.tax_id)
        self.assertEqual(self.order_01.amount_untaxed, 70)
        self.assertEqual(self.order_01.amount_tax, 9.80)
        self.assertEqual(self.order_01.amount_total, 79.80)
        self.assertIn(self.tax_4, self.order_line_2_1.tax_id)
        self.assertIn(self.tax_10, self.order_line_2_1.tax_id)
        self.assertIn(self.tax_4, self.order_line_2_2.tax_id)
        self.assertIn(self.tax_10, self.order_line_2_2.tax_id)
        self.assertEqual(self.order_02.amount_untaxed, 100)
        self.assertEqual(self.order_02.amount_tax, 14)
        self.assertEqual(self.order_02.amount_total, 114)
