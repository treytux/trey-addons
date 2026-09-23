###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductBarcodeAuto(TransactionCase):

    def test_barcode_auto_assignment(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertTrue(product.barcode)
        product.write({'barcode': False})
        self.assertTrue(product.barcode)
        self.assertEqual(len(product.barcode), 13)
        self.assertTrue(product.barcode.startswith('84999'))
        product.barcode = '999'
        self.assertEqual(product.barcode, '999')

    def test_barcode_copy_and_variant(self):
        product_template = self.env['product.template'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'barcode': '000',
        })
        product = product_template.product_variant_id
        self.assertEqual(product.barcode, '000')
        copy_product = product.copy()
        self.assertTrue(copy_product.barcode)
        self.assertIn(str(copy_product.id), copy_product.barcode)

    def test_barcode_duplicate_barcode(self):
        self.env['product.template'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'barcode': '000',
        })
        with self.assertRaises(ValidationError):
            self.env['product.template'].create({
                'type': 'service',
                'company_id': False,
                'name': 'Test product 2',
                'standard_price': 10,
                'list_price': 100,
                'barcode': '000',
            })
