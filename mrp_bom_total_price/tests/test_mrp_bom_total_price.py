# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase


class TestMrpBomTotalPrice(TransactionCase):

    def setUp(self):
        super(TestMrpBomTotalPrice, self).setUp()
        product_obj = self.env['product.product']
        self.product1 = product_obj.create({
            'name': 'Component Product',
            'lst_price': 10.0,
            'standard_price': 5.0,
        })
        self.product2 = product_obj.create({
            'name': 'BoM Product',
        })
        self.bom = self.env['mrp.bom'].create({
            'product_id': self.product2.id,
            'product_tmpl_id': self.product2.product_tmpl_id.id,
            'bom_line_ids': [(0, 0, {'product_id': self.product1.id,
                                     'product_qty': 10.0})]
        })

    def test_mrp_bom_total_price(self):
        line = self.bom.bom_line_ids[:1]
        self.assertEquals(
            self.product1.lst_price, line.lst_price)
        self.assertEquals(
            self.product1.standard_price, line.standard_price)
        self.assertEquals(
            self.product1.lst_price * line.product_qty, line.bom_lst_price)
        self.assertEquals(
            self.product1.standard_price * line.product_qty,
            line.bom_prod_price)
        self.assertEquals(len(self.bom.bom_line_ids), 1)
        self.assertEquals(self.bom.bom_prod_price_total, line.bom_prod_price)
        self.assertEquals(self.bom.bom_lst_price_total, line.bom_lst_price)
