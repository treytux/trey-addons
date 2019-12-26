###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase


class TestWebsiteProductMultiwebsite(HttpCase):

    def setUp(self):
        super().setUp()
        self.product = self.env.ref(
            'product.product_product_3_product_template').product_variant_id
        self.site1 = self.env['website'].create({
            'name': 'Site One'})
        self.site2 = self.env['website'].create({
            'name': 'Site Two'})

    def test_one_product_two_sites(self):
        obj = self.product.product_tmpl_id.with_context(
            website_id=self.site1.id)
        access = obj.can_access_from_current_website
        self.product.website_ids = [(6, 0, [self.site1.id, self.site2.id])]
        self.assertTrue(access(self.site1.id))
        self.assertTrue(access())
        self.product.website_ids = [(6, 0, [self.site2.id])]
        self.assertFalse(access(self.site1.id))
        self.assertFalse(access())
        self.product.website_ids = [(6, 0, [])]
        self.assertTrue(access(self.site1.id))
        self.assertTrue(access(self.site2.id))
        self.assertTrue(access())
