###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductInactiveTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_1 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 100,
        })

        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        self.product_tmpl_2 = self.env['product.template'].create({
            'name': 'Test product 2',
            'type': 'service',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 3)

    def test_write_default_behavior_without_variants(self):
        self.assertTrue(self.product_1.product_tmpl_id.active)
        self.assertTrue(self.product_1.active)
        self.product_1.product_tmpl_id.active = False
        self.assertFalse(self.product_1.product_tmpl_id.active)
        self.assertFalse(self.product_1.active)

    def test_write_default_behavior_with_variants(self):
        self.assertTrue(self.product_tmpl_2.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 3)
        for variant in self.product_tmpl_2.product_variant_ids:
            self.assertTrue(variant.active)
        self.product_tmpl_2.active = False
        self.assertFalse(self.product_tmpl_2.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 0)

    def test_write_inactive_product_without_variants(self):
        self.assertTrue(self.product_1.active)
        self.assertTrue(self.product_1.product_tmpl_id.active)
        self.product_1.active = False
        self.assertFalse(self.product_1.active)
        self.assertFalse(self.product_1.product_tmpl_id.active)

    def test_write_inactive_product_with_variants(self):
        self.assertTrue(self.product_tmpl_2.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 3)
        product_variant_1 = self.product_tmpl_2.product_variant_ids[0]
        self.assertTrue(product_variant_1.active)
        self.assertTrue(product_variant_1.product_tmpl_id.active)
        product_variant_1.active = False
        self.assertFalse(product_variant_1.active)
        self.assertTrue(product_variant_1.product_tmpl_id.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 2)
        product_variant_2 = self.product_tmpl_2.product_variant_ids[0]
        product_variant_2.active = False
        self.assertFalse(product_variant_2.active)
        self.assertTrue(product_variant_2.product_tmpl_id.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 1)
        product_variant_3 = self.product_tmpl_2.product_variant_ids[0]
        product_variant_3.active = False
        self.assertFalse(product_variant_3.active)
        self.assertFalse(product_variant_3.product_tmpl_id.active)
