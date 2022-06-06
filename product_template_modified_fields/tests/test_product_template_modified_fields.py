###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo.tests.common import TransactionCase


class TestProductTemplateModifiedFields(TransactionCase):

    def test_product_template(self):
        user = self.env.ref('base.partner_admin')
        product_obj = self.env['product.template'].sudo(user.id).with_context(
            mail_create_nolog=True)
        product = product_obj.create({
            'name': 'Test produc',
            'type': 'service',
            'default_code': 'DEFAULTCODE',
            'standard_price': 100,
            'list_price': 200,
        })
        product.last_modified_fields = False
        self.assertFalse(product.last_modified_fields)
        product.name = 'Other name'
        self.assertTrue(product.last_modified_fields)
        data = json.loads(product.last_modified_fields)
        self.assertEquals(data, ['name'])
