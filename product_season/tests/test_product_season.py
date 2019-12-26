###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProductSeason(common.TransactionCase):

    def setUp(self):
        super(TestProductSeason, self).setUp()
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
