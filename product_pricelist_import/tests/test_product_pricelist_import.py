###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import os
import base64


class TestProductPricelistImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product1 = self.env.ref(
            'product.product_product_1_product_template')
        self.product1.default_code = 'TEST_P1'
        self.product2 = self.env.ref(
            'product.product_product_2_product_template')
        self.product2.default_code = 'TEST_P2'
        self.pl_items = self.env['product.pricelist'].create({
            'name': 'Test pricelist import, with items',
            'import_code': 'items'})
        self.pl_items.item_ids = [
            (0, 0, {
                'product_tmpl_id': self.product1.id,
                'applied_on': '1_product',
                'min_quantity': 1,
                'compute_price': 'fixed',
                'fixed_price': float(1)}),
            (0, 0, {
                'product_tmpl_id': self.product2.id,
                'applied_on': '1_product',
                'min_quantity': 1,
                'compute_price': 'fixed',
                'fixed_price': float(2)})]
        self.pl_empty = self.env['product.pricelist'].create({
            'name': 'Test pricelist import, empty',
            'import_code': 'empty'})

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def test_constraint_code(self):
        pl_test = self.pl_items.copy()
        self.assertEquals(pl_test.import_code, False)
        self.assertRaises(Exception, pl_test.write, {'import_code': 'items'})

    def test_product_import(self):
        fname = self.get_sample('sample_ok.xlsx')
        self.env['product.pricelist'].import_excel(fname)
        self.assertEquals(len(self.pl_items.item_ids), 3)
        self.assertEquals(
            self.pl_items.item_ids[0].product_tmpl_id, self.product1)
        self.assertEquals(self.pl_items.item_ids[0].fixed_price, 11.11)
        self.assertEquals(
            self.pl_items.item_ids[1].product_tmpl_id, self.product2)
        self.assertEquals(self.pl_items.item_ids[1].fixed_price, 22.22)
        self.assertEquals(len(self.pl_empty.item_ids), 3)
        self.assertEquals(
            self.pl_empty.item_ids[0].product_tmpl_id, self.product1)
        self.assertEquals(self.pl_empty.item_ids[0].fixed_price, 33.33)
        self.assertEquals(
            self.pl_empty.item_ids[1].product_tmpl_id, self.product2)
        self.assertEquals(self.pl_empty.item_ids[1].fixed_price, 44.44)

    def test_more_that_one_item(self):
        self.pl_items.item_ids = [
            (0, 0, {
                'product_tmpl_id': self.product1.id,
                'applied_on': '1_product',
                'min_quantity': 1,
                'compute_price': 'fixed',
                'fixed_price': float(1)}),
            (0, 0, {
                'product_tmpl_id': self.product2.id,
                'applied_on': '1_product',
                'min_quantity': 1,
                'compute_price': 'fixed',
                'fixed_price': float(2)})]
        self.assertEquals(len(self.pl_items.item_ids), 5)
        fname = self.get_sample('sample_ok.xlsx')
        self.env['product.pricelist'].import_excel(fname)
        self.assertEquals(len(self.pl_items.item_ids), 5)
        self.assertEquals(
            self.pl_items.item_ids[0].product_tmpl_id, self.product1)
        self.assertEquals(self.pl_items.item_ids[0].fixed_price, 11.11)
        self.assertEquals(
            self.pl_items.item_ids[1].product_tmpl_id, self.product2)
        self.assertEquals(self.pl_items.item_ids[1].fixed_price, 22.22)
        self.assertEquals(
            self.pl_items.item_ids[2].product_tmpl_id, self.product1)
        self.assertEquals(self.pl_items.item_ids[2].fixed_price, 11.11)
        self.assertEquals(
            self.pl_items.item_ids[3].product_tmpl_id, self.product2)
        self.assertEquals(self.pl_items.item_ids[3].fixed_price, 22.22)

    def test_import_wizard(self):
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['product.pricelist.import'].create(
            {'data_file': file})
        wizard.import_file()

    def test_error_values(self):
        self.assertEquals(len(self.pl_items.item_ids), 3)
        fname = self.get_sample('sample_error_values.xlsx')
        self.assertRaises(
            UserError, self.env['product.pricelist'].import_excel, fname)

    def test_error_empty_columns(self):
        self.assertEquals(len(self.pl_items.item_ids), 3)
        fname = self.get_sample('sample_empty_columns.xlsx')
        self.env['product.pricelist'].import_excel(fname)

    def test_update_prices(self):
        fname = self.get_sample('sample_update_prices.xlsx')
        self.env['product.pricelist'].import_excel(fname)
        self.assertEquals(round(self.product1.list_price, 2), 12.12)
        self.assertEquals(round(self.product1.standard_price, 2), 10.10)
