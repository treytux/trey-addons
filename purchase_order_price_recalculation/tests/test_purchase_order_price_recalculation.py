# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.tests.common as common
from openerp import fields


class TestPurchaseOrderPriceRecalculation(common.TransactionCase):

    def setUp(self):
        super(TestPurchaseOrderPriceRecalculation, self).setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner 01',
            'supplier': True})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product',
            'list_price': 100,
            'standard_price': 90})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id})
        self.purchase_order_01 = self.env['purchase.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('purchase.list0'),
            'location_id': self.ref('stock.stock_location_suppliers'),
            'order_line': [
                (0, 0, {'product_id': self.pp_01.id,
                        'name': self.pp_01.name,
                        'product_qty': 1.0,
                        'price_unit': self.pp_01.standard_price,
                        'date_planned': fields.Date.today()})]})

    def test_price_recalculation(self):
        purchase_line = self.purchase_order_01.order_line[0]
        purchase_line.name = 'My product description'
        self.assertEqual(purchase_line.price_unit, self.pp_01.standard_price)
        self.pp_01.standard_price = 50
        self.purchase_order_01.recalculate_prices()
        self.assertEqual(purchase_line.price_unit, self.pp_01.standard_price)
        self.assertEqual(purchase_line.product_qty, 1)
        self.assertEqual(purchase_line.name, 'My product description')
