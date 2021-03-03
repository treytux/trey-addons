###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductGet(TransactionCase):

    def test_product_pattern(self):
        tmpl = self.env['product.template'].create({
            'type': 'service',
            'company_id': False,
            'default_code': 'pt.code',
            'name': 'pt.name',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEquals(tmpl.name_get()[0][1], 'pt.name')
        attr = self.env['product.attribute'].create({
            'name': 'Attribute',
        })
        value1 = self.env['product.attribute.value'].create({
            'name': 'V1',
            'attribute_id': attr.id,
        })
        value2 = self.env['product.attribute.value'].create({
            'name': 'V2',
            'attribute_id': attr.id,
        })
        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': tmpl.id,
            'attribute_id': attr.id,
            'value_ids': [(6, 0, [value1.id, value2.id])],
        })
        variant = tmpl.product_variant_id
        self.assertEquals(variant.name_get()[0][1], 'pt.name')
