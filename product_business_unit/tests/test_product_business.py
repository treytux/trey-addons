###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestProductBusiness(TransactionCase):

    def setUp(self):
        super().setUp()
        self.unit_a = self.env['product.business.unit'].create({
            'name': 'Business unit A'
        })
        self.area_a = self.env['product.business.area'].create({
            'name': 'Area A',
            'unit_id': self.unit_a.id,
        })
        self.unit_b = self.env['product.business.unit'].create({
            'name': 'Business unit B'
        })
        self.area_b = self.env['product.business.area'].create({
            'name': 'Area B',
            'unit_id': self.unit_b.id,
        })

    def create_product_template(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product',
            'area_id': self.area_a.id,
        })
        self.assertEquals(product.unit_id, self.area_a.unit_id)
        self.assertEquals(
            product.business_display_name,
            self.env['product.template'].business_display_name(product))
        self.assertRaises(
            ValidationError, product.write, [{'area_id': self.area_2.id}])
        self.assertRaises(
            ValidationError, product.write, [{'unit_id': self.unit_2.id}])
