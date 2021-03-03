###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductGet(TransactionCase):

    def test_product_pattern(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'default_code': 'pp.code',
            'name': 'pp.name',
            'standard_price': 10,
            'list_price': 100,
        })
        tmpl = product.product_tmpl_id
        tmpl.name = 'pt.name'
        value = tmpl._name_get_parse('%(product_tmpl_id.name)s', product)
        self.assertEquals(value, 'pt.name')
        value = tmpl._name_get_parse(
            '%(default_code)s-%(product_tmpl_id.name)s', product)
        self.assertEquals(value, 'pp.code-pt.name')
        value = tmpl._name_get_parse('%(xxx)s', product)
        self.assertEquals(value, '%(xxx)s')
        value = tmpl._name_get_parse('%(product_tmpl_id.xxx)s', product)
        self.assertEquals(value, '%(product_tmpl_id.xxx)s')

    def test_product_get(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'default_code': 'pp.code',
            'name': 'pp.name',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertEquals(product.name, 'pp.name')
        self.assertEquals(product.product_tmpl_id.name, 'pp.name')
        product_pattern = self.env.ref(
            'product_name_get.product_product_name_pattern')
        product_pattern.value = '%(name)s'
        self.assertEquals(product.name_get()[0][1], 'pp.name')
        tmpl_pattern = self.env.ref(
            'product_name_get.product_template_name_pattern')
        tmpl_pattern.value = '%(default_code)s-%(name)s'
        self.assertEquals(
            product.product_tmpl_id.name_get()[0][1], 'pp.code-pp.name')

    def test_product_get_variants(self):
        tmpl = self.env['product.template'].create({
            'type': 'service',
            'company_id': False,
            'default_code': 'pt.code',
            'name': 'pt.name',
            'standard_price': 10,
            'list_price': 100,
        })
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
        self.assertEquals(variant._name, 'product.product')
        product_pattern = self.env.ref(
            'product_name_get.product_product_name_pattern')
        product_pattern.value = ''
        self.assertEquals(variant.name_get()[0][1], '[pt.code] pt.name')
        product_pattern.value = '%(product_tmpl_id.name)s %(name)s'
        self.assertEquals(variant.name_get()[0][1], 'pt.name pt.name')
        product_pattern.value = '%(name)s'
        self.assertEquals(variant.name_get()[0][1], 'pt.name')
