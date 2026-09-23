###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging
from datetime import timedelta

from odoo import fields
from odoo.tests import common

_log = logging.getLogger(__name__)

try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class TestStockInventoryValuedExport(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 1',
            'standard_price': 90,
            'list_price': 100,
        })
        self.category_all = self.env.ref('product.product_category_all')
        self.categ_1 = self.env['product.category'].create({
            'name': 'Categ 1',
            'parent_id': self.category_all.id,
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 2',
            'standard_price': 33,
            'list_price': 50,
            'categ_id': self.categ_1.id,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.stock_sublocation_1 = self.env['stock.location'].create({
            'name': 'Stock sublocation 1',
            'usage': 'internal',
            'location_id': self.stock_location.id,
        })
        self.stock_sublocation_2 = self.env['stock.location'].create({
            'name': 'Stock sublocation 2',
            'usage': 'internal',
            'location_id': self.stock_location.id,
        })
        self.location_no_parent = self.env['stock.location'].create({
            'name': 'Test internal location',
            'usage': 'internal',
        })

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_export_stock_inventory_valued_current_date(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 10)
        self.update_qty_on_hand(self.product_1, self.stock_sublocation_1, 20)
        self.update_qty_on_hand(self.product_1, self.stock_sublocation_2, 30)
        self.update_qty_on_hand(self.product_1, self.location_no_parent, 1)
        wizard = self.env['stock.inventory.valued.export'].create({
            'compute_at_date': 0,
        })
        wizard.action_accept()
        self.assertTrue(wizard.data_file)
        buf = io.BytesIO()
        buf.write(base64.b64decode(wizard.data_file))
        buf.seek(0)
        df = pd.read_excel(
            buf, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        cols = df.axes[1]
        rows_len = len(df.axes[0])
        cols_len = len(df.axes[1])
        self.assertEqual(cols_len, 6)
        self.assertEqual(cols[0], 'Product')
        self.assertEqual(cols[1], 'Product category')
        self.assertEqual(cols[2], 'Location')
        self.assertEqual(cols[3], 'Quantity')
        self.assertEqual(cols[4], 'Standard price')
        self.assertEqual(cols[5], 'Subtotal')
        for row_number in range(0, rows_len - 1):
            product_name = df.iloc[row_number][0]
            product_categ = df.iloc[row_number][1]
            location_name = df.iloc[row_number][2]
            quantity = df.iloc[row_number][3]
            standard_price = df.iloc[row_number][4]
            price_subtotal = df.iloc[row_number][5]
            if product_name == 'Product test 1':
                self.assertEquals(product_categ, 'All')
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(quantity, 60)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 60 * 90)
                elif location_name == self.stock_sublocation_1.complete_name:
                    self.assertEqual(quantity, 20)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 20 * 90)
                elif location_name == self.stock_sublocation_2.complete_name:
                    self.assertEqual(quantity, 30)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 30 * 90)
                elif location_name == self.location_no_parent.complete_name:
                    self.assertEqual(quantity, 1)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 1 * 90)
            elif product_name == 'Product test 2':
                self.assertEquals(product_categ, 'All / Categ 1')
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(quantity, 300)
                    self.assertEqual(standard_price, 33)
                    self.assertEqual(price_subtotal, 300 * 33)
                elif location_name == self.stock_sublocation_1.complete_name:
                    self.assertEqual(quantity, 200)
                    self.assertEqual(standard_price, 33)
                    self.assertEqual(price_subtotal, 200 * 33)
                elif location_name == self.location_no_parent.complete_name:
                    self.assertEqual(quantity, 2)
                    self.assertEqual(standard_price, 33)
                    self.assertEqual(price_subtotal, 2 * 33)
        total = df.iloc[rows_len - 1][cols_len - 1]
        self.assertGreater(total, 0)

    def test_export_stock_inventory_valued_specific_date(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 10)
        self.update_qty_on_hand(self.product_1, self.stock_sublocation_1, 20)
        self.update_qty_on_hand(self.product_1, self.stock_sublocation_2, 30)
        self.update_qty_on_hand(self.product_1, self.location_no_parent, 1)
        self.update_qty_on_hand(self.product_2, self.stock_location, 100)
        self.update_qty_on_hand(self.product_2, self.stock_sublocation_1, 200)
        self.update_qty_on_hand(self.product_2, self.location_no_parent, 2)
        moves = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
            ('product_uom_qty', '=', 10),
            ('location_dest_id', '=', self.stock_location.id),
        ])
        self.assertEqual(len(moves), 1)
        moves[0].date = fields.Datetime.now() - timedelta(days=15)
        moves = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
            ('product_uom_qty', '=', 1),
            ('location_dest_id', '=', self.location_no_parent.id),
        ])
        self.assertEqual(len(moves), 1)
        moves[0].date = fields.Datetime.now() - timedelta(days=15)
        wizard = self.env['stock.inventory.valued.export'].create({
            'compute_at_date': 1,
            'date': fields.Datetime.now() - timedelta(days=10),
        })
        wizard.action_accept()
        self.assertTrue(wizard.data_file)
        buf = io.BytesIO()
        buf.write(base64.b64decode(wizard.data_file))
        buf.seek(0)
        df = pd.read_excel(
            buf, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        cols = df.axes[1]
        rows_len = len(df.axes[0])
        cols_len = len(df.axes[1])
        self.assertEqual(cols_len, 6)
        self.assertEqual(cols[0], 'Product')
        self.assertEqual(cols[1], 'Product category')
        self.assertEqual(cols[2], 'Location')
        self.assertEqual(cols[3], 'Quantity')
        self.assertEqual(cols[4], 'Standard price')
        self.assertEqual(cols[5], 'Subtotal')
        for row_number in range(0, rows_len - 1):
            product_name = df.iloc[row_number][0]
            product_categ = df.iloc[row_number][1]
            location_name = df.iloc[row_number][2]
            quantity = df.iloc[row_number][3]
            standard_price = df.iloc[row_number][4]
            price_subtotal = df.iloc[row_number][5]
            if product_name == 'Product test 1':
                self.assertEquals(product_categ, 'All')
                self.assertNotEquals(
                    location_name, self.stock_sublocation_1.complete_name)
                self.assertNotEquals(
                    location_name, self.stock_sublocation_2.complete_name)
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(quantity, 10)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 10 * 90)
                elif location_name == self.location_no_parent.complete_name:
                    self.assertEqual(quantity, 1)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 1 * 90)
        total = df.iloc[rows_len - 1][cols_len - 1]
        self.assertGreater(total, 0)
