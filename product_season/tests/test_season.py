# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import logging
_log = logging.getLogger(__name__)


class TestSeason(common.TransactionCase):

    def setUp(self):
        super(TestSeason, self).setUp()
        self.products = []
        for k in ['One', 'Two', 'Three']:
            self.products.append(self.env['product.product'].create({
                'name': 'Product %s Test' % k,
                'type': 'product'}))
        self.winter = self.env['product.season'].create({
            'name': 'Winter'})
        self.summer = self.env['product.season'].create({
            'name': 'Summer'})

    def create_invoice(self, lines):
        self.assertFalse(self.winter.product_tmpl_ids)
        for p in self.products:
            p.season_id = self.winter.id
        self.assertTrue(self.winter.product_tmpl_ids)
        self.assertEqual(self.product_tmpl_count, 3)
