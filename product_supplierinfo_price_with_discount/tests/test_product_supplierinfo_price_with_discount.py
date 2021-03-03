# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.tests.common as common


class TestProductSupplierinfoPriceWithDiscount(common.TransactionCase):

    def setUp(self):
        super(TestProductSupplierinfoPriceWithDiscount, self).setUp()
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Supplier 01',
            'supplier': True,
        })
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product',
        })
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'standard_price': 22,
            'list_price': 33,
        })

    def create_product_supplierinfo(self, lines):
        return self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id,
            'pricelist_ids': lines,
        })

    def test_compute_unit_price_without_pricelists(self):
        supplierinfo = self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.pt_01.id,
            'name': self.supplier_01.id,
        })
        self.assertEqual(len(supplierinfo.pricelist_ids), 0)
        self.assertEqual(supplierinfo.unit_price, 0.0)
        self.assertEqual(supplierinfo.unit_price_note, '-')

    def test_compute_unit_price_without_discount(self):
        lines = [
            (0, 0, {
                'min_quantity': 0,
                'price': 10,
                'discount': 0,
            })]
        supplierinfo = self.create_product_supplierinfo(lines)
        self.assertEqual(supplierinfo.unit_price, 10.0)
        self.assertEqual(supplierinfo.unit_price_note, '>=0.0 : 10.0')

    def test_compute_unit_price_with_discount(self):
        lines = [
            (0, 0, {
                'min_quantity': 0,
                'price': 10,
                'discount': 30,
            })]
        supplierinfo = self.create_product_supplierinfo(lines)
        self.assertEqual(supplierinfo.unit_price, 10.0)
        self.assertEqual(supplierinfo.unit_price_note, '>=0.0 : 7.0')

    def test_compute_unit_price_without_discount_several_pricelists(self):
        lines = [
            (0, 0, {
                'min_quantity': 0,
                'price': 10,
                'discount': 0,
            }),
            (0, 0, {
                'min_quantity': 1,
                'price': 20,
                'discount': 0,
            }),
        ]
        supplierinfo = self.create_product_supplierinfo(lines)
        self.assertEqual(supplierinfo.unit_price, 10.0)
        self.assertEqual(
            supplierinfo.unit_price_note, '0.0 - 0.999 :  10.0\n>=1.0 : 20.0')

    def test_compute_unit_price_with_discount_several_pricelists(self):
        lines = [
            (0, 0, {
                'min_quantity': 0,
                'price': 10,
                'discount': 30,
            }),
            (0, 0, {
                'min_quantity': 1,
                'price': 20,
                'discount': 50,
            }),
        ]
        supplierinfo = self.create_product_supplierinfo(lines)
        self.assertEqual(supplierinfo.unit_price, 10.0)
        self.assertEqual(
            supplierinfo.unit_price_note, '0.0 - 0.999 :  7.0\n>=1.0 : 10.0')
