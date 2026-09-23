###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestProductBarcodeGeneratorById(TransactionCase):

    def setUp(self):
        super().setUp()
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        self.test_sequence_category = self.env['ir.sequence'].create({
            'name': 'Product barcode seq category',
            'code': 'product.barcode.test',
            'prefix': 'Cat',
            'padding': 5,
        })
        self.test_sequence_company = self.env['ir.sequence'].create({
            'name': 'Product barcode seq company',
            'code': 'product.barcode.test',
            'prefix': 'Com',
            'padding': 5,
        })
        self.category = self.env['product.category'].create({
            'name': 'Test Category',
            'barcode_sequence_id': self.test_sequence_category.id,
        })
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'barcode_sequence_id': self.test_sequence_company.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'detailed_type': 'consu',
            'categ_id': self.category.id,
            'company_id': self.company.id,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'list_price': 100.0,
            'default_code': 'TEST-001',
        })

    def test_barcode_generated(self):
        self.product.barcode = self.product._get_barcode_next_code(
            self.product)
        self.assertEqual(
            self.product.barcode, 'CatCom' + f'{self.product.id:012d}')
