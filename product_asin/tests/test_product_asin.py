###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestProductAsin(common.TransactionCase):

    def test_product_asin(self):
        template = self.env['product.template'].create({
            'name': 'Product Test',
            'asin': 'ASIN-01',
        })
        self.assertEquals(template.asin, 'ASIN-01')
        self.assertEquals(template.product_variant_id.asin, 'ASIN-01')
        with self.assertRaises(exceptions.ValidationError):
            self.env['product.template'].create({
                'name': 'Other Product Test',
                'asin': 'ASIN-01',
            })
        template2 = self.env['product.template'].create({
            'name': 'Other Product Test',
            'asin': 'ASIN-02',
        })
        product = self.env['product.product'].search(
            [('asin', '=', 'ASIN-02')])
        self.assertEquals(product.product_tmpl_id, template2)
