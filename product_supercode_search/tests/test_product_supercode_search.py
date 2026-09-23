###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductSupercodeSearch(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Vendor One',
            'ref': 'V-001',
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer One',
            'ref': 'C-001',
        })

    def test_template_supercode(self):
        template = self.env['product.template'].create({
            'name': 'Blue Chair',
            'default_code': 'CHAIR-01',
            'barcode': '8400000000017',
            'seller_ids': [(0, 0, {
                'partner_id': self.partner.id,
                'product_code': 'SUP-CHAIR',
            })],
        })
        self.assertIn('Blue Chair', template.supercode)
        self.assertIn('CHAIR-01', template.supercode)
        self.assertIn('8400000000017', template.supercode)
        self.assertIn('Vendor One', template.supercode)
        self.assertIn('V-001', template.supercode)
        self.assertIn('SUP-CHAIR', template.supercode)

    def test_template_supercode_includes_customer(self):
        template = self.env['product.template'].create({
            'name': 'Green Sofa',
            'default_code': 'SOFA-01',
            'customer_ids': [(0, 0, {
                'partner_id': self.customer.id,
                'product_code': 'CUST-SOFA',
            })],
        })
        self.assertIn('Customer One', template.supercode)
        self.assertIn('C-001', template.supercode)
        self.assertIn('CUST-SOFA', template.supercode)

    def test_product_supercode_customer_specific(self):
        template = self.env['product.template'].create({
            'name': 'White Cabinet',
            'default_code': 'CAB-01',
        })
        product = template.product_variant_id
        self.env['product.customerinfo'].create({
            'partner_id': self.customer.id,
            'product_tmpl_id': template.id,
            'product_id': product.id,
            'product_code': 'CUST-CAB',
        })
        self.assertIn('Customer One', product.supercode)
        self.assertIn('C-001', product.supercode)
        self.assertIn('CUST-CAB', product.supercode)

    def test_product_supercode_includes_template(self):
        template = self.env['product.template'].create({
            'name': 'Red Table',
            'default_code': 'TABLE-01',
        })
        product = template.product_variant_id
        self.assertIn(template.supercode, product.supercode)
        self.assertIn('TABLE-01', product.supercode)

    def test_supercode_recompute_on_variant_code(self):
        template = self.env['product.template'].create({
            'name': 'Lamp',
            'default_code': 'LAMP-01',
        })
        product = template.product_variant_id
        product.default_code = 'LAMP-99'
        self.assertIn('LAMP-99', template.supercode)
        self.assertIn('LAMP-99', product.supercode)

    def test_search_by_supercode(self):
        template = self.env['product.template'].create({
            'name': 'Desk',
            'default_code': 'DESK-77',
        })
        found = self.env['product.template'].search([
            ('supercode', 'ilike', 'DESK-77'),
        ])
        self.assertIn(template, found)
        variant = template.product_variant_id
        found_variant = self.env['product.product'].search([
            ('supercode', 'ilike', 'DESK-77'),
        ])
        self.assertIn(variant, found_variant)
