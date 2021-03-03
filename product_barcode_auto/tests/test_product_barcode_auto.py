###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductBarcodeAuto(TransactionCase):

    def test_barcode(self):
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
        self.assertEquals(len(product.barcode), 13)
        self.assertTrue(product.barcode.startswith('84999'))
        product.barcode = '999'
        self.assertEquals(product.barcode, '999')
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'barcode': '000',
        })
        self.assertEquals(product.barcode, '000')
        copy_product = product.copy()
        self.assertTrue(copy_product.barcode)
        self.assertTrue(str(copy_product.id) in copy_product.barcode)
