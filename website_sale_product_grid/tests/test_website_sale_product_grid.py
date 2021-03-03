###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale_product_grid.controllers.main import WebsiteSale
from odoo.tests.common import HttpCase


class TestProductGet(HttpCase):

    def setUp(self):
        super().setUp()
        self.tmpl = self.env['product.template'].create({
            'type': 'product',
            'default_code': 'code',
            'name': 'T-Shirt',
            'website_published': True,
        })
        self.size = self.env['product.attribute'].create({
            'name': 'Size',
            'type': 'select',
            'sequence': 1,
        })
        self.create_attr_values(self.size, ['M', 'L', 'XL', 'XXL'])
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.tmpl.id,
            'attribute_id': self.size.id,
            'value_ids': [(6, 0, self.size.value_ids.ids)],
        })
        self.color = self.env['product.attribute'].create({
            'name': 'Color',
            'type': 'color',
            'sequence': 2,
        })
        self.create_attr_values(self.color, ['Black', 'Withe'])
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.tmpl.id,
            'attribute_id': self.color.id,
            'value_ids': [(6, 0, self.color.value_ids.ids)],
        })
        self.tmpl.create_variant_ids()

    def create_attr_values(self, attr, values):
        for value in values:
            self.env['product.attribute.value'].create({
                'name': value,
                'attribute_id': attr.id,
            })

    def test_product_and_variants(self):
        self.assertEquals(len(self.tmpl.attribute_line_ids), 2)
        self.assertEquals(
            len(self.tmpl.attribute_line_ids.mapped('value_ids.id')), 6)
        self.assertEquals(len(self.tmpl.product_variant_ids), 8)

    def test_fill_grid(self):
        controller = WebsiteSale()
        grid = controller._fill_grid(self.tmpl, self.size)
        for value in self.color.value_ids:
            key = '%s-%s' % (self.tmpl.id, value.id)
            self.assertIn(key, grid)
            self.assertTrue(grid[key]['default'])

    def test_fill_grid_3(self):
        gender = self.env['product.attribute'].create({
            'name': 'Gender',
            'type': 'select',
            'sequence': 3,
        })
        self.create_attr_values(gender, ['Man', 'Woman'])
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.tmpl.id,
            'attribute_id': gender.id,
            'value_ids': [(6, 0, gender.value_ids.ids)],
        })
        self.tmpl.create_variant_ids()
        self.assertEquals(len(self.tmpl.product_variant_ids), 16)
        controller = WebsiteSale()
        grid = controller._fill_grid(self.tmpl, self.size)
        for color_value in self.color.value_ids:
            for gender_value in gender.value_ids:
                key = '%s-%s' % (
                    self.tmpl.id,
                    '-'.join([str(color_value.id), str(gender_value.id)]))
                self.assertIn(key, grid)
                self.assertTrue(grid[key]['default'])

    def test_controller(self):
        response = self.url_open('/shop/product/%s' % self.tmpl.id)
        self.assertEquals(response.status_code, 200)
