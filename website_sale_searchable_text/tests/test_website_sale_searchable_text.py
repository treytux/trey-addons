###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestWebsiteSaleSearchableText(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['White', 'Black']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr.id,
                'name': value,
            })
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test product 1',
            'type': 'service',
            'standard_price': 10.00,
            'company_id': False,
            'default_code': 'T0001',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })

    def test_compute_searchable_text(self):
        self.assertEquals(len(self.product_tmpl.product_variant_ids), 2)
        product_01 = (
            self.product_tmpl.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids.name == 'White'))
        self.assertEquals(len(product_01), 1)
        product_02 = (
            self.product_tmpl.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids.name == 'Black'))
        self.assertEquals(len(product_02), 1)
        self.assertEquals(
            self.product_tmpl.searchable_text,
            'Test product 1   ')
        self.product_tmpl.name = 'Test 1'
        self.assertEquals(
            self.product_tmpl.searchable_text,
            'Test 1   ')
        self.product_tmpl.website_description = 'Website description'
        self.product_tmpl.hidden_mapping = 'Hidden mapping'
        self.assertEquals(
            self.product_tmpl.searchable_text,
            'Test 1 Website description Hidden mapping ')
        product_01.default_code = 'DFC01'
        product_02.default_code = 'DFC02'
        self.assertEquals(
            self.product_tmpl.searchable_text,
            'Test 1 Website description Hidden mapping DFC01 DFC02')
        product_01.default_code = 'CODE1'
        product_02.default_code = 'CODE2'
        self.assertEquals(
            self.product_tmpl.searchable_text,
            'Test 1 Website description Hidden mapping CODE1 CODE2')
