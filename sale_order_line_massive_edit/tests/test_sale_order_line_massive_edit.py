# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import logging
_log = logging.getLogger(__name__)


class TestSaleOrderLineMassiveEdit(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderLineMassiveEdit, self).setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': 10})
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'service'})
        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id,
            'list_price': 20})
        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0')})
        self.order_line_01 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'name': self.pp_01.name_template,
            'product_id': self.pp_01.id,
            'product_uom_qty': 2,
            'price_unit': self.pp_01.list_price,
            'product_uom': self.ref('product.product_uom_unit')})

    def test_update_product(self):
        self.order_01.action_lines_massive_edit()
        current_wiz = self.env['wiz.sale_order_line_edit'].search(
            [], order='id desc', limit=1)
        current_wiz.line_ids[0].product_id = self.pp_02.id
        current_wiz.button_accept()
        self.assertEqual(self.order_line_01.product_id, self.pp_02)
        self.assertEqual(self.order_line_01.product_uom_qty, 2)
        self.assertEqual(self.order_line_01.price_unit, 10)
        self.assertEqual(self.order_line_01.discount, 0)
        self.assertEqual(self.order_line_01.price_subtotal, 20)
        self.assertEqual(self.order_01.amount_total, 20)

    def test_update_quantity(self):
        self.order_01.action_lines_massive_edit()
        current_wiz = self.env['wiz.sale_order_line_edit'].search(
            [], order='id desc', limit=1)
        current_wiz.line_ids[0].quantity = 5
        current_wiz.button_accept()
        self.assertEqual(self.order_line_01.product_id, self.pp_01)
        self.assertEqual(self.order_line_01.product_uom_qty, 5)
        self.assertEqual(self.order_line_01.price_unit, 10)
        self.assertEqual(self.order_line_01.discount, 0)
        self.assertEqual(self.order_line_01.price_subtotal, 50)
        self.assertEqual(self.order_01.amount_total, 50)

    def test_update_price_unit(self):
        self.order_01.action_lines_massive_edit()
        current_wiz = self.env['wiz.sale_order_line_edit'].search(
            [], order='id desc', limit=1)
        current_wiz.line_ids[0].price_unit = 100
        current_wiz.button_accept()
        self.assertEqual(self.order_line_01.product_id, self.pp_01)
        self.assertEqual(self.order_line_01.product_uom_qty, 2)
        self.assertEqual(self.order_line_01.price_unit, 100)
        self.assertEqual(self.order_line_01.discount, 0)
        self.assertEqual(self.order_line_01.price_subtotal, 200)
        self.assertEqual(self.order_01.amount_total, 200)

    def test_update_discount(self):
        self.order_01.action_lines_massive_edit()
        current_wiz = self.env['wiz.sale_order_line_edit'].search(
            [], order='id desc', limit=1)
        current_wiz.line_ids[0].discount = 50
        current_wiz.button_accept()
        self.assertEqual(self.order_line_01.product_id, self.pp_01)
        self.assertEqual(self.order_line_01.product_uom_qty, 2)
        self.assertEqual(self.order_line_01.price_unit, 10)
        self.assertEqual(self.order_line_01.discount, 50)
        self.assertEqual(self.order_line_01.price_subtotal, 10)
        self.assertEqual(self.order_01.amount_total, 10)
