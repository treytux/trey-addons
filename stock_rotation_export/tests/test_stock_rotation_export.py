###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class TestStockRotationExport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.customer = self.env['res.partner'].create({
            'name': 'Customer test',
            'customer': True,
        })
        self.supplier_1 = self.env['res.partner'].create({
            'name': 'Supplier test 1',
            'supplier': True,
        })
        self.supplier_2 = self.env['res.partner'].create({
            'name': 'Supplier test 2',
            'supplier': True,
        })
        self.supplier_3 = self.env['res.partner'].create({
            'name': 'Supplier test 3',
            'supplier': True,
        })
        self.category_all = self.env.ref('product.product_category_all')
        self.categ_1 = self.env['product.category'].create({
            'name': 'Categ 1',
            'parent_id': self.category_all.id,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 1',
            'default_code': 'PROD1',
            'categ_id': self.category_all.id,
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 2',
            'default_code': 'PROD2',
            'categ_id': self.categ_1.id,
            'standard_price': 20,
            'list_price': 200,
        })
        self.warehouse_1 = self.env.ref('stock.warehouse0')
        self.stock_location = self.warehouse_1.lot_stock_id
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.inventory_loc = self.env.ref('stock.location_inventory')
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        self.stock_location_2 = self.warehouse_2.lot_stock_id
        self.today = fields.Date.today()

    def create_purchase(self, partner, picking_type, product, qty):
        purchase = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'picking_type_id': picking_type.id,
        })
        purchase.onchange_partner_id()
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'product_uom_qty': qty,
        })
        line.onchange_product_id()
        line['price_unit'] = 100
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        return purchase

    def create_sale(self, partner, warehouse, product, qty):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'warehouse_id': warehouse.id,
        })
        sale.onchange_partner_id()
        vline = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': product.list_price,
        })
        vline.product_id_change()
        self.env['sale.order.line'].create(
            vline._convert_to_write(vline._cache))
        sale.action_confirm()
        return sale

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEqual(
            product.with_context(location=location.id).qty_available, new_qty)

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()

    def test_check_constraint_dates(self):
        with self.assertRaises(ValidationError) as result:
            self.env['stock.rotation.export'].create({
                'date_from': self.today,
                'date_to': self.today + timedelta(days=1),
            })
        self.assertEqual(
            result.exception.name,
            'Dates must not be later than the current date.')
        with self.assertRaises(ValidationError) as result:
            self.env['stock.rotation.export'].create({
                'date_from': self.today - timedelta(days=5),
                'date_to': self.today - timedelta(days=10),
            })
        self.assertEqual(
            result.exception.name,
            'The "From date" must be less than the "To date".')

    # Caso 1 excel:
    # stock previo   0
    # compramos    100
    # vendemos     150
    def test_stock_rotation_export_01(self):
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_from,
            ).qty_available, 0
        )
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 100)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 100)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 150)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, -50)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0.67)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 150)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -100)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 2 excel:
    # stock previo  50
    # compramos      0
    # vendemos     100
    def test_stock_rotation_export_02(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 50)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 100)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 100)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, -50)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0.5)
                    self.assertEqual(stock_date_from, 50)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 100)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -50)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 3 excel:
    # stock previo  20
    # compramos    100
    # vendemos      60
    def test_stock_rotation_export_03(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 20)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 120)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 60)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 60)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to
            ).qty_available, 60)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 2)
                    self.assertEqual(stock_date_from, 20)
                    self.assertEqual(stock_date_to, 60)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 60)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -100)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -20)
                    self.assertEqual(stock_date_to, -20)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 4 excel:
    # stock previo   0
    # compramos    100
    # vendemos       1
    def test_stock_rotation_export_04(self):
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_from,
            ).qty_available, 0
        )
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 100)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 99)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': self.today,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 100)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 99)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 1)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -100)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 5 excel:
    # stock previo 100
    # compramos      0
    # vendemos      10
    def test_stock_rotation_export_05(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 100)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 100)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 10)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 10)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 90)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 10)
                    self.assertEqual(stock_date_from, 100)
                    self.assertEqual(stock_date_to, 90)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 10)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -100)
                    self.assertEqual(stock_date_to, -100)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 6:
    # stock previo            0
    # compramos             100
    # dev de clientes         1
    # vendemos              150
    # dev de proveedores      2
    def test_stock_rotation_export_06_returns(self):
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_from,
            ).qty_available, 0
        )
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 100)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 100)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 150)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, -50)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, -49)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, -51)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0.66)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -51)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 150)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -98)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 149)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 7:
    # stock previo           50
    # compramos             100
    # dev de clientes         1
    # vendemos               10
    # dev de proveedores      2
    def test_stock_rotation_export_07_return(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 50)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 150)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 10)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 10)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 140)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 141)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 139)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 12.58)
                    self.assertEqual(stock_date_from, 50)
                    self.assertEqual(stock_date_to, 139)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 10)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -50)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -98)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 8:
    # - Product 1:
    # stock previo   0
    # compramos    100
    # vendemos     150
    # - Product 2:
    # stock previo   0
    # compramos     10
    # vendemos       1
    def test_stock_rotation_export_08_several_products(self):
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_from,
            ).qty_available, 0
        )
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 100)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 100)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 150)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, -50)
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id,
                to_date=date_from,
            ).qty_available, 0
        )
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_2, 10)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 10)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 10)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_2, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 9)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0.67)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 150)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -100)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
            elif product_name == 'Product test 2':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 10)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 10)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 1)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -10)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 9:
    # - Product 1:
    # stock previo           50
    # compramos             100
    # dev de clientes         1
    # vendemos               10
    # dev de proveedores      2
    # - Product 2:
    # stock previo           25
    # compramos              10
    # dev de clientes         1
    # vendemos                1
    # dev de proveedores      2
    def test_stock_rotation_export_09_several_products_return(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 50)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 150)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 10)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 10)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 140)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 141)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 139)
        self.update_qty_on_hand(self.product_2, self.stock_location, 25)
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_2.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_2, 10)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 10)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_2, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 34)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 35)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 33)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': self.today,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 12.58)
                    self.assertEqual(stock_date_from, 50)
                    self.assertEqual(stock_date_to, 139)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 10)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -50)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -98)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
            elif product_name == 'Product test 2':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 12)
                    self.assertEqual(stock_date_from, 25)
                    self.assertEqual(stock_date_to, 33)
                    self.assertEqual(buyed, 10)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 1)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -25)
                    self.assertEqual(stock_date_to, -25)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -8)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 0)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 10:
    # stock previo (WH/Stock)       0
    # compramos (WH/Stock)        100
    # vendemos (WH/Stock)         150
    # stock previo (WH/Stock2)     10
    # vendemos (WH/stock2)          1
    def test_stock_rotation_export_10_several_warehouses(self):
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_from,
            ).qty_available, 0
        )
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id,
            self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id,
            self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 100)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 100)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 150)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, -50)
        self.update_qty_on_hand(self.product_1, self.stock_location_2, 10)
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        sale = self.create_sale(
            self.customer, self.warehouse_2, self.product_1, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location_2.id,
                to_date=date_to,
            ).qty_available, 9)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0.67)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 150)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.stock_location_2.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 10)
                    self.assertEqual(stock_date_from, 10)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 1)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -10)
                    self.assertEqual(stock_date_to, -10)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -100)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 11:
    # - Product 1:
    # stock previo           50
    # compramos             100
    # dev de clientes         1
    # vendemos               10(4+6)
    # dev de proveedores      2
    # - Product 2:
    # stock previo           25
    # compramos              10
    # dev de clientes         1
    # vendemos                1
    # dev de proveedores      2
    def test_stock_rotation_export_11_several_sales_products_return(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 50)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 150)
        sale_1 = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 4)
        picking_out = sale_1.picking_ids
        self.picking_transfer(picking_out, 4)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 146)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 147)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 145)
        sale_2 = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 6)
        picking_out = sale_2.picking_ids
        self.picking_transfer(picking_out, 6)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 139)
        self.update_qty_on_hand(self.product_2, self.stock_location, 25)
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_2.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_2, 10)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 10)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_2, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 34)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 35)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 33)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': self.today,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 12.58)
                    self.assertEqual(stock_date_from, 50)
                    self.assertEqual(stock_date_to, 139)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 10)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -50)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -98)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
            elif product_name == 'Product test 2':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 12)
                    self.assertEqual(stock_date_from, 25)
                    self.assertEqual(stock_date_to, 33)
                    self.assertEqual(buyed, 10)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 1)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -25)
                    self.assertEqual(stock_date_to, -25)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -8)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD2')
                    self.assertEqual(category, 'All / Categ 1')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 0)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 12:
    # stock previo (WH/Stock)       0
    # compramos (WH/Stock)        100
    # vendemos (WH/Stock)         150 (100+50)
    # stock previo (WH/Stock2)     10
    # vendemos (WH/stock2)          1
    def test_stock_rotation_export_10_several_sales_warehouses(self):
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_from,
            ).qty_available, 0
        )
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id,
            self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id,
            self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 100)
        sale_1 = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 100)
        picking_out = sale_1.picking_ids
        self.picking_transfer(picking_out, 100)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 0)
        sale_2 = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 50)
        picking_out = sale_2.picking_ids
        self.picking_transfer(picking_out, 50)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, -50)
        self.update_qty_on_hand(self.product_1, self.stock_location_2, 10)
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        sale = self.create_sale(
            self.customer, self.warehouse_2, self.product_1, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location_2.id,
                to_date=date_to,
            ).qty_available, 9)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': date_to,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0.67)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 150)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.stock_location_2.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 10)
                    self.assertEqual(stock_date_from, 10)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 1)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -10)
                    self.assertEqual(stock_date_to, -10)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -100)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)

    # Caso 9 pero con filtro de supplier
    # - Product 1 (supplier_1/product_tmpl_1):
    # stock previo           50
    # compramos             100
    # dev de clientes         1
    # vendemos               10
    # dev de proveedores      2
    # - Product 2 (supplier_2/product_tmpl_2):
    # stock previo           25
    # compramos              10
    # dev de clientes         1
    # vendemos                1
    # dev de proveedores      2
    def test_stock_rotation_export_09_several_products_supplier_tmpl_filter(
            self):
        self.env['product.supplierinfo'].create({
            'name': self.supplier_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
        })
        self.env['product.supplierinfo'].create({
            'name': self.supplier_2.id,
            'product_tmpl_id': self.product_2.product_tmpl_id.id,
        })
        self.update_qty_on_hand(self.product_1, self.stock_location, 50)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_2, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 150)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 10)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 10)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 140)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 141)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 139)
        self.update_qty_on_hand(self.product_2, self.stock_location, 25)
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_2.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_2, 10)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 10)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_2, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 34)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 35)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 33)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': self.today,
            'supplier_id': self.supplier_1.id,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 12.58)
                    self.assertEqual(stock_date_from, 50)
                    self.assertEqual(stock_date_to, 139)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 10)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -50)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -98)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                self.assertNotEqual(product_name, 'Product test 2')

    # Caso 9 pero con filtro de supplier
    # - Product 1 (supplier_1/product_1):
    # stock previo           50
    # compramos             100
    # dev de clientes         1
    # vendemos               10
    # dev de proveedores      2
    # - Product 2 (supplier_2/product_2):
    # stock previo           25
    # compramos              10
    # dev de clientes         1
    # vendemos                1
    # dev de proveedores      2
    def test_stock_rotation_export_09_several_products_supplier_product_filter(
            self):
        self.env['product.supplierinfo'].create({
            'name': self.supplier_1.id,
            'product_id': self.product_1.id,
        })
        self.env['product.supplierinfo'].create({
            'name': self.supplier_2.id,
            'product_id': self.product_2.id,
        })
        self.update_qty_on_hand(self.product_1, self.stock_location, 50)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_2, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 150)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 10)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 10)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 140)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 141)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 139)
        self.update_qty_on_hand(self.product_2, self.stock_location, 25)
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_2.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_2, 10)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 10)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_2, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 34)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 35)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 33)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': self.today,
            'supplier_id': self.supplier_1.id,
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
        self.assertEqual(cols_len, 11)
        self.assertEqual(cols[0], 'Product default code')
        self.assertEqual(cols[1], 'Product name')
        self.assertEqual(cols[2], 'Category')
        self.assertEqual(cols[3], 'Location')
        self.assertEqual(cols[4], 'Ratio')
        self.assertEqual(cols[5], 'Stock in date from')
        self.assertEqual(cols[6], 'Stock in date to')
        self.assertEqual(cols[7], 'Buyed')
        self.assertEqual(cols[8], 'Customer return')
        self.assertEqual(cols[9], 'Sold')
        self.assertEqual(cols[10], 'Supplier return')
        for row_number in range(0, rows_len):
            product_default_code = df.iloc[row_number][0]
            product_name = df.iloc[row_number][1]
            category = df.iloc[row_number][2]
            location_name = df.iloc[row_number][3]
            ratio = df.iloc[row_number][4]
            stock_date_from = df.iloc[row_number][5]
            stock_date_to = df.iloc[row_number][6]
            buyed = df.iloc[row_number][7]
            customer_return = df.iloc[row_number][8]
            sold = df.iloc[row_number][9]
            supplier_return = df.iloc[row_number][10]
            if product_name == 'Product test 1':
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 12.58)
                    self.assertEqual(stock_date_from, 50)
                    self.assertEqual(stock_date_to, 139)
                    self.assertEqual(buyed, 100)
                    self.assertEqual(customer_return, 1)
                    self.assertEqual(sold, 10)
                    self.assertEqual(supplier_return, 2)
                elif location_name == self.inventory_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, -50)
                    self.assertEqual(stock_date_to, -50)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.supplier_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, -98)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                elif location_name == self.customer_loc.complete_name:
                    self.assertEqual(product_default_code, 'PROD1')
                    self.assertEqual(category, 'All')
                    self.assertEqual(ratio, 0)
                    self.assertEqual(stock_date_from, 0)
                    self.assertEqual(stock_date_to, 9)
                    self.assertEqual(buyed, 0)
                    self.assertEqual(customer_return, 0)
                    self.assertEqual(sold, 0)
                    self.assertEqual(supplier_return, 0)
                self.assertNotEqual(product_name, 'Product test 2')

    # Caso 9 pero con filtro de supplier no encontrado
    # - Product 1 (supplier_1/product_1):
    # stock previo           50
    # compramos             100
    # dev de clientes         1
    # vendemos               10
    # dev de proveedores      2
    # - Product 2 (supplier_2/product_2):
    # stock previo           25
    # compramos              10
    # dev de clientes         1
    # vendemos                1
    # dev de proveedores      2
    def test_stock_rotation_export_09_several_products_supplier_not_found(
            self):
        self.env['product.supplierinfo'].create({
            'name': self.supplier_1.id,
            'product_id': self.product_1.id,
        })
        self.env['product.supplierinfo'].create({
            'name': self.supplier_2.id,
            'product_id': self.product_2.id,
        })
        self.update_qty_on_hand(self.product_1, self.stock_location, 50)
        date_from = self.today - timedelta(days=7)
        date_to = self.today
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 20)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 20)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        purchase_2 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_1, 80)
        picking_in_2 = purchase_2.picking_ids
        self.picking_transfer(picking_in_2, 80)
        self.assertEquals(picking_in_2.state, 'done')
        picking_in_2.move_lines.date = (
            picking_in_2.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 150)
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_1, 10)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 10)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 140)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id).qty_available, 141)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_1.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 139)
        self.update_qty_on_hand(self.product_2, self.stock_location, 25)
        last_move = self.env['stock.move'].search([
            ('product_id', '=', self.product_2.id),
        ], order='id desc', limit=1)
        last_move.write({
            'date': date_from,
        })
        purchase_1 = self.create_purchase(
            self.supplier_1, self.warehouse_1.in_type_id, self.product_2, 10)
        picking_in_1 = purchase_1.picking_ids
        self.picking_transfer(picking_in_1, 10)
        self.assertEquals(picking_in_1.state, 'done')
        picking_in_1.move_lines.date = (
            picking_in_1.move_lines.date - timedelta(days=5))
        sale = self.create_sale(
            self.customer, self.warehouse_1, self.product_2, 1)
        picking_out = sale.picking_ids
        self.picking_transfer(picking_out, 1)
        picking_out.move_lines.date = (
            picking_out.move_lines.date - timedelta(days=5))
        self.assertEquals(picking_out.state, 'done')
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 34)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out.ids,
            active_id=picking_out.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=5))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id).qty_available, 35)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids,
            active_id=picking_in_1.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(return_pick.state, 'done')
        return_pick.move_lines.date = (
            return_pick.move_lines.date - timedelta(days=3))
        self.assertEqual(
            self.product_2.with_context(
                location=self.stock_location.id,
                to_date=date_to,
            ).qty_available, 33)
        wizard = self.env['stock.rotation.export'].create({
            'date_from': date_from,
            'date_to': self.today,
            'supplier_id': self.supplier_3.id,
        })
        with self.assertRaises(ValidationError) as result:
            wizard.action_accept()
        self.assertEqual(
            result.exception.name,
            'No product associated with the selected supplier '
            '\'Supplier test 3\' has been found.')
