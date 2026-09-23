from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductTemplateBuilder(TransactionCase):
    def setUp(self):
        super().setUp()
        template_builder_obj = self.env['product.template.builder']
        self.product_template_builder = template_builder_obj.create({
            'name': 'Test Product Template Builder',
            'sale_ok': True,
            'purchase_ok': True,
            'type': 'consu',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        self.default = self.env['ir.default'].create({
            'field_id': self.env.ref(
                'product_template_builder.field_product_template__product_temp'
                'late_builder_id').id,
            'json_value': self.product_template_builder.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
        })

    def test_default_product_template(self):
        self.assertEqual(
            self.product.categ_id, self.product_template_builder.categ_id)
        self.assertEqual(
            self.product.uom_id, self.product_template_builder.uom_id)
        self.assertEqual(
            self.product.type, self.product_template_builder.type)

    def test_archive_product_template(self):
        with self.assertRaises(UserError):
            self.product_template_builder.write({'active': False})
