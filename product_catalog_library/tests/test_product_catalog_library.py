###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductCatalogLibrary(TransactionCase):

    def setUp(self):
        super().setUp()
        self.line_model = self.env['product.catalog.line']

    def test_product_code_is_supplier_ref_plus_default_code(self):
        line = self.line_model.create_from_row({
            'line_num': 2,
            'default_code': 'ABC',
            'supplier_ref': 'SUP-',
            'name': 'Test product',
        })
        self.assertEqual(line.product_code, 'SUP-ABC')

    def test_activate_variant_group_activates_all_lines(self):
        values = [
            {
                'line_num': 2,
                'default_code': 'RED',
                'product_code': 'SUP-RED',
                'ean': '8400000000011',
                'name': 'Test shirt',
                'product_tmpl_code': 'SHIRT',
                'attribute:Color': 'Red',
            },
            {
                'line_num': 3,
                'default_code': 'BLUE',
                'product_code': 'SUP-BLUE',
                'ean': '8400000000028',
                'name': 'Test shirt',
                'product_tmpl_code': 'SHIRT',
                'attribute:Color': 'Blue',
            },
        ]
        lines = self.line_model.browse()
        for value in values:
            value['source_data'] = value.copy()
            lines |= self.line_model.create_from_row(value)
        lines[0].action_activate()
        self.assertTrue(all(lines.mapped(lambda line: line.state == 'active')))
        self.assertEqual(
            lines.mapped('product_tmpl_id'), lines[0].product_tmpl_id)
        self.assertEqual(len(lines[0].product_tmpl_id.product_variant_ids), 2)
        variants = lines[0].product_tmpl_id.product_variant_ids
        self.assertTrue(all(variants.mapped('active')))

    def test_activate_existing_product_prefers_ean(self):
        product = self.env['product.product'].create({
            'name': 'Existing product',
            'default_code': 'OLD-CODE',
            'barcode': '8400000000035',
        })
        line = self.line_model.create_from_row({
            'line_num': 2,
            'default_code': 'NEW',
            'product_code': 'NEW-CODE',
            'ean': product.barcode,
            'name': 'Updated product',
        })
        line.action_activate()
        self.assertEqual(line.product_id, product)
        self.assertEqual(line.product_id.default_code, 'NEW-CODE')
