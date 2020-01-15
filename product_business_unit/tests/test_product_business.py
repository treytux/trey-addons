###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductBusiness(TransactionCase):

    def setUp(self):
        super().setUp()
        unit_obj = self.env['product.business.unit']
        self.unit1 = unit_obj.create({'name': 'Business unit 1'})
        self.unit2 = unit_obj.create({'name': 'Business unit 2'})
        area_obj = self.env['product.business.area']
        self.area1a = area_obj.create({
            'name': 'Unit 1a',
            'unit_id': self.unit1.id,
        })
        self.area2a = area_obj.create({
            'name': 'Unit 2a',
            'unit_id': self.unit2.id,
        })

    def test_product_unit_and_area_integrity(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product',
            'area_id': self.area2a.id,
        })
        self.assertEquals(product.unit_id, self.unit2)
        self.assertEquals(product.area_id, self.area2a)
        product.area_id = self.area1a
        self.assertEquals(product.unit_id, self.unit1)
        self.assertEquals(product.area_id, self.area1a)
        product.unit_id = self.unit2
        self.assertEquals(product.unit_id, self.unit2)
        self.assertEquals(bool(product.area_id), False)

    def test_product_only_with_unit_integrity(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product',
            'unit_id': self.unit1.id,
        })
        self.assertEquals(product.unit_id, self.unit1)
        self.assertEquals(bool(product.area_id), False)
        product.area_id = self.area1a
        self.assertEquals(product.unit_id, self.unit1)
        self.assertEquals(product.area_id, self.area1a)
        product.unit_id = self.unit2
        self.assertEquals(product.unit_id, self.unit2)
        self.assertEquals(bool(product.area_id), False)
