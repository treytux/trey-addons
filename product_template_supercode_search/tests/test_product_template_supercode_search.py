###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProductTemplateSupercodeSearch(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_tmpl = self.env['product.template'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Consu product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.partner_supplier = self.env['res.partner'].create({
            'name': 'Partner supplier',
        })
        self.partner_customer = self.env['res.partner'].create({
            'name': 'Partner customer',
        })

    def test_compute_update_supercode(self):
        self.product_tmpl.default_code = '1234'
        self.assertIn(
            self.product_tmpl.default_code, self.product_tmpl.supercode)
        customer_info = self.env['product.customerinfo'].create({
            'name': self.partner_customer.id,
            'product_tmpl_id': self.product_tmpl.id,
            'min_qty': 0.0,
            'price': 200,
        })
        self.assertIn(customer_info.name.name, self.product_tmpl.supercode)
        supplier_info = self.env['product.supplierinfo'].create({
            'name': self.partner_supplier.id,
            'product_tmpl_id': self.product_tmpl.id,
            'min_qty': 0.0,
            'price': 100,
        })
        self.assertIn(supplier_info.name.name, self.product_tmpl.supercode)
        self.product_tmpl.barcode = 'Barcode test'
        self.assertIn(
            self.product_tmpl.barcode, self.product_tmpl.supercode)

    def test_name_search(self):
        self.product_tmpl.default_code = '0000'
        self.assertEquals(len(self.product_tmpl.name_search('0000')), 1)
