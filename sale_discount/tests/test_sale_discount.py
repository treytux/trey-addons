# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, exceptions


class TestSaleDiscount(common.TransactionCase):

    def setUp(self):
        super(TestSaleDiscount, self).setUp()
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
        self.pt_04 = self.env['product.template'].create({
            'name': 'Product not apply discount',
            'apply_sale_discount': False,
            'type': 'consu',
            'taxes_id': [(6, 0, [self.taxs_21.id])]})
        self.pp_04 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_04.id,
            'list_price': 10})
        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.order_line_01 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'name': self.pp_01.name_template,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.list_price,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21.id])]})
        self.order_02 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.order_line_02 = self.env['sale.order.line'].create({
            'order_id': self.order_02.id,
            'name': self.pp_01.name_template,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.list_price,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21.id])]})
        self.order_03 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'section_id': self.ref('sales_team.section_sales_department'),
            'date_order': fields.Date.today()})
        self.order_line_03 = self.env['sale.order.line'].create({
            'order_id': self.order_03.id,
            'product_id': self.pp_01.id,
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21[0].id])]})
        self.order_04 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.order_line_04_01 = self.env['sale.order.line'].create({
            'order_id': self.order_04.id,
            'name': self.pp_01.name_template,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.list_price,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21.id])]})
        self.order_line_04_02 = self.env['sale.order.line'].create({
            'order_id': self.order_04.id,
            'product_id': self.pp_04.id,
            'name': self.pp_04.name_template,
            'price_unit': self.pp_04.list_price,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21[0].id])]})
        self.order_05 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today()})
        self.order_line_05_01 = self.env['sale.order.line'].create({
            'order_id': self.order_05.id,
            'name': self.pp_01.name_template,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.list_price,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21.id])]})
        self.order_line_05_02 = self.env['sale.order.line'].create({
            'order_id': self.order_05.id,
            'name': 'Without product',
            'price_unit': 10,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21[0].id])]})

    def test_sale_discount_percent_line_apply(self):
        self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_01.ids,
            'active_model': 'sale.order',
            'active_id': self.order_01.id}).create({
                'discount_type': 'percent_line',
                'discount_applied': 10.0}).button_accept()
        self.order_01.button_dummy()
        self.assertEqual(self.order_line_01.discount, 10)
        self.assertEqual(self.order_line_01.price_subtotal, 9)
        self.assertEqual(self.order_01.amount_untaxed, 9)
        self.assertEqual(self.order_01.amount_tax, 1.89)
        self.assertEqual(self.order_01.amount_total, 10.89)

    def test_sale_discount_percent_total_error(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 333.0})
        wiz.product_id = wiz.product_id_change()
        self.assertRaises(Exception, wiz.button_accept)

    def test_sale_discount_percent_line_not_apply_sale_discount(self):
        self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_04.ids,
            'active_model': 'sale.order',
            'active_id': self.order_04.id}).create({
                'discount_type': 'percent_line',
                'discount_applied': 10.0}).button_accept()
        self.order_04.button_dummy()
        self.assertEqual(self.order_line_04_01.discount, 10)
        self.assertEqual(self.order_line_04_01.price_subtotal, 9)
        self.assertEqual(self.order_line_04_02.discount, 0)
        self.assertEqual(self.order_line_04_02.price_subtotal, 10)
        self.assertEqual(self.order_04.amount_untaxed, 19)
        self.assertEqual(self.order_04.amount_tax, 3.99)
        self.assertEqual(self.order_04.amount_total, 22.99)

    def test_sale_discount_percent_line_apply_no_product(self):
        self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_05.ids,
            'active_model': 'sale.order',
            'active_id': self.order_05.id}).create({
                'discount_type': 'percent_line',
                'discount_applied': 10.0}).button_accept()
        self.order_05.button_dummy()
        self.assertEqual(self.order_line_05_01.discount, 10)
        self.assertEqual(self.order_line_05_01.price_subtotal, 9)
        self.assertEqual(self.order_line_05_02.discount, 10)
        self.assertEqual(self.order_line_05_02.price_subtotal, 9)
        self.assertEqual(self.order_05.amount_untaxed, 18)
        self.assertEqual(self.order_05.amount_tax, 3.78)
        self.assertEqual(self.order_05.amount_total, 21.78)

    def test_sale_discount_percent_total_product_without_taxs(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 10.0})
        wiz.product_id = wiz.product_id_change()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_taxes, self.pp_02.product_tmpl_id.taxes_id)
        self.order_02.button_dummy()
        self.assertEqual(self.order_02.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_02.order_line[1].price_subtotal, -1)
        self.assertEqual(self.order_02.amount_untaxed, 9)
        self.assertEqual(self.order_02.amount_tax, 2.1)
        self.assertEqual(self.order_02.amount_total, 11.1)

    def test_sale_discount_percent_total_product_with_taxs(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_03.id,
                'discount_applied': 10.0})
        wiz.product_id = wiz.product_id_change()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_taxes, self.pp_03.product_tmpl_id.taxes_id)
        self.order_02.button_dummy()
        self.assertEqual(self.order_02.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_02.order_line[1].price_subtotal, -1)
        self.assertEqual(self.order_02.amount_untaxed, 9)
        self.assertEqual(self.order_02.amount_tax, 1.89)
        self.assertEqual(self.order_02.amount_total, 10.89)

    def test_sale_discount_percent_total_with_discount_tax(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 10.0,
                'discount_taxes': [(6, 0, [self.taxs_10.id])]})
        wiz.button_accept()
        self.assertEqual(wiz.discount_taxes, self.taxs_10)
        self.order_02.button_dummy()
        self.assertEqual(self.order_02.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_02.order_line[1].price_subtotal, -1)
        self.assertEqual(self.order_02.amount_untaxed, 9)
        self.assertEqual(self.order_02.amount_tax, 2)
        self.assertEqual(self.order_02.amount_total, 11)

    def test_sale_discount_percent_total_with_discount_taxs(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_02.ids,
            'active_model': 'sale.order',
            'active_id': self.order_02.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_02.id,
                'discount_applied': 10.0,
                'discount_taxes': [
                    (6, 0, [self.taxs_10.id, self.taxs_21.id])]})
        wiz.button_accept()
        self.assertIn(self.taxs_10, wiz.discount_taxes)
        self.assertIn(self.taxs_21, wiz.discount_taxes)
        self.order_02.button_dummy()
        self.assertEqual(self.order_02.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_02.order_line[1].price_subtotal, -1)
        self.assertEqual(self.order_02.amount_untaxed, 9)
        self.assertEqual(self.order_02.amount_tax, 1.79)
        self.assertEqual(self.order_02.amount_total, 10.79)

    def test_sale_discount_percent_total_not_apply_sale_discount(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_04.ids,
            'active_model': 'sale.order',
            'active_id': self.order_04.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_03.id,
                'discount_applied': 10.0})
        wiz.product_id = wiz.product_id_change()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_taxes, self.pp_03.product_tmpl_id.taxes_id)
        self.order_04.button_dummy()
        self.assertEqual(self.order_04.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_04.order_line[1].price_subtotal, 10)
        self.assertEqual(self.order_04.order_line[2].price_subtotal, -1)
        self.assertEqual(self.order_04.amount_untaxed, 19)
        self.assertEqual(self.order_04.amount_tax, 3.99)
        self.assertEqual(self.order_04.amount_total, 22.99)

    def test_sale_discount_percent_total_apply_no_product(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_05.ids,
            'active_model': 'sale.order',
            'active_id': self.order_05.id}).create({
                'discount_type': 'percent_total',
                'product_id': self.pp_03.id,
                'discount_applied': 10.0})
        wiz.product_id = wiz.product_id_change()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_taxes, self.pp_03.product_tmpl_id.taxes_id)
        self.order_05.button_dummy()
        self.assertEqual(self.order_05.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_05.order_line[1].price_subtotal, 10)
        self.assertEqual(self.order_05.order_line[2].price_subtotal, -2)
        self.assertEqual(self.order_05.amount_untaxed, 18)
        self.assertEqual(self.order_05.amount_tax, 3.78)
        self.assertEqual(self.order_05.amount_total, 21.78)

    def test_sale_discount_quantity_total_product_without_taxs(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'discount_type': 'quantity_total',
                'discount_quantity': 1,
                'product_id': self.pp_02.id})
        wiz.product_id = wiz.product_id_change()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_taxes, self.pp_02.product_tmpl_id.taxes_id)
        self.order_03.button_dummy()
        self.assertEqual(self.order_03.amount_untaxed, 9)
        self.assertEqual(self.order_03.amount_tax, 2.1)
        self.assertEqual(self.order_03.amount_total, 11.1)

    def test_sale_discount_quantity_total_product_with_taxs(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'discount_type': 'quantity_total',
                'discount_quantity': 1,
                'product_id': self.pp_02.id})
        wiz.button_accept()
        wiz.product_id = wiz.product_id_change()
        self.order_03.button_dummy()
        self.assertEqual(self.order_03.amount_untaxed, 9)
        self.assertEqual(self.order_03.amount_tax, 2.1)
        self.assertEqual(self.order_03.amount_total, 11.1)

    def test_sale_discount_quantity_total_with_discount_tax(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_02.id,
                'discount_quantity': 1,
                'discount_taxes': [(6, 0, [self.taxs_10.id])]})
        wiz.button_accept()
        self.assertEqual(wiz.discount_taxes, self.taxs_10)
        self.order_03.button_dummy()
        self.assertEqual(self.order_03.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_03.order_line[1].price_subtotal, -1)
        self.assertEqual(self.order_03.amount_untaxed, 9)
        self.assertEqual(self.order_03.amount_tax, 2)
        self.assertEqual(self.order_03.amount_total, 11)

    def test_sale_discount_quantity_total_with_discount_taxs(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_02.id,
                'discount_quantity': 1,
                'discount_taxes': [
                    (6, 0, [self.taxs_10.id, self.taxs_21.id])]})
        wiz.button_accept()
        self.assertIn(self.taxs_10, wiz.discount_taxes)
        self.assertIn(self.taxs_21, wiz.discount_taxes)
        self.order_03.button_dummy()
        self.assertEqual(self.order_03.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_03.order_line[1].price_subtotal, -1)
        self.assertEqual(self.order_03.amount_untaxed, 9)
        self.assertEqual(self.order_03.amount_tax, 1.79)
        self.assertEqual(self.order_03.amount_total, 10.79)

    def test_sale_discount_quantity_total_with_discount_taxs_no_draft(self):
        self.order_03.action_cancel()
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_03.ids,
            'active_model': 'sale.order',
            'active_id': self.order_03.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_02.id,
                'discount_quantity': 1,
                'discount_taxes': [
                    (6, 0, [self.taxs_10.id, self.taxs_21.id])]})
        self.assertRaises(Exception, wiz.button_accept)

    def test_sale_discount_quantity_total_not_apply_sale_discount(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_04.ids,
            'active_model': 'sale.order',
            'active_id': self.order_04.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_03.id,
                'discount_quantity': 1})
        wiz.product_id = wiz.product_id_change()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_taxes, self.pp_03.product_tmpl_id.taxes_id)
        self.order_04.button_dummy()
        self.assertEqual(self.order_04.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_04.order_line[1].price_subtotal, 10)
        self.assertEqual(self.order_04.order_line[2].price_subtotal, -1)
        self.assertEqual(self.order_04.amount_untaxed, 19)
        self.assertEqual(self.order_04.amount_tax, 3.99)
        self.assertEqual(self.order_04.amount_total, 22.99)

    def test_sale_discount_quantity_total_apply_no_product(self):
        wiz = self.env['wiz.sale.discount'].with_context({
            'active_ids': self.order_05.ids,
            'active_model': 'sale.order',
            'active_id': self.order_05.id}).create({
                'discount_type': 'quantity_total',
                'product_id': self.pp_03.id,
                'discount_quantity': 1})
        wiz.product_id = wiz.product_id_change()
        wiz.button_accept()
        self.assertEqual(
            wiz.discount_taxes, self.pp_03.product_tmpl_id.taxes_id)
        self.order_05.button_dummy()
        self.assertEqual(self.order_05.order_line[0].price_subtotal, 10)
        self.assertEqual(self.order_05.order_line[1].price_subtotal, 10)
        self.assertEqual(self.order_05.order_line[2].price_subtotal, -1)
        self.assertEqual(self.order_05.amount_untaxed, 19)
        self.assertEqual(self.order_05.amount_tax, 3.99)
        self.assertEqual(self.order_05.amount_total, 22.99)
