# ###############################################################################
# # For copyright and license notices, see __manifest__.py file in root directory
# ###############################################################################
import base64
import io
import logging
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import common

_log = logging.getLogger(__name__)

try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class TestStockInventoryValuedExportExtend(common.TransactionCase):

    def setUp(self):
        super().setUp()
        product_attribute = self.env['product.attribute'].create({
            'name': 'Color',
        })
        product_attribute_1 = self.env['product.attribute'].create({
            'name': 'Size',
        })
        product_attribute_value = self.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': product_attribute.id,
        })
        product_attribute_value_2 = self.env['product.attribute.value'].create({
            'name': 'L',
            'attribute_id': product_attribute_1.id,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 1',
            'standard_price': 90,
            'list_price': 100,
            'description': 'Description for Product test 1',
            'attribute_value_ids': [
                (4, product_attribute_value.id),
                (4, product_attribute_value_2.id)],
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
            'attribute_value_ids': [(4, product_attribute_value.id)],
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
        self.env['stock.warehouse.orderpoint'].create({
            'product_id': self.product_1.id,
            'location_id': self.stock_location.id,
            'product_min_qty': 10,
            'product_max_qty': 100,
        })
        self.env['stock.warehouse.orderpoint'].create({
            'product_id': self.product_1.id,
            'location_id': self.stock_sublocation_1.id,
            'product_min_qty': 20,
            'product_max_qty': 200,
        })
        self.env['stock.warehouse.orderpoint'].create({
            'product_id': self.product_1.id,
            'location_id': self.stock_sublocation_2.id,
            'product_min_qty': 30,
            'product_max_qty': 300,
        })
        self.env['stock.warehouse.orderpoint'].create({
            'product_id': self.product_1.id,
            'location_id': self.location_no_parent.id,
            'product_min_qty': 40,
            'product_max_qty': 400,
        })

    def create_sale_order(self, product, qty):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.env.user.partner_id.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'price_unit': product.list_price,
                    'name': product.name,
                })
            ],
            'picking_policy': 'direct',
        })
        sale_order.action_confirm()

    def create_purchase_order(self, product, qty):
        po = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'order_line': [
                (0, 0, {
                    'name': product.name,
                    'product_id': product.id,
                    'product_qty': qty,
                    'product_uom': self.env.ref(
                        'uom.product_uom_unit').id,
                    'price_unit': 121.0,
                    'date_planned': datetime.today(),
                })],
        })
        po.button_confirm()

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
        self.update_qty_on_hand(self.product_1, self.location_no_parent, 18)
        self.update_qty_on_hand(self.product_2, self.stock_location, 100)
        self.update_qty_on_hand(self.product_2, self.stock_sublocation_1, 200)
        self.update_qty_on_hand(self.product_2, self.location_no_parent, 55)
        self.create_sale_order(self.product_1, 10)
        self.create_sale_order(self.product_2, 15)
        self.create_purchase_order(self.product_1, 15)
        self.create_purchase_order(self.product_2, 20)
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
        self.assertEqual(cols_len, 21)
        self.assertEqual(cols[0], 'Product')
        self.assertEqual(cols[1], 'Product category')
        self.assertEqual(cols[2], 'Location')
        self.assertEqual(cols[3], 'Quantity')
        self.assertEqual(cols[4], 'Standard price')
        self.assertEqual(cols[5], 'Subtotal')
        self.assertEqual(cols[6], 'Description')
        self.assertEqual(cols[7], 'Attribute')
        self.assertEqual(cols[8], 'Pending to send')
        self.assertEqual(cols[9], 'Net stock')
        self.assertEqual(cols[10], 'Pending to receive')
        self.assertEqual(cols[11], 'Stock provided')
        self.assertEqual(cols[12], 'Last departure')
        self.assertEqual(cols[13], 'Last entry')
        self.assertEqual(cols[14], 'Sales current month')
        self.assertEqual(cols[15], 'Sales last month')
        self.assertEqual(cols[16], 'Average last 12 months')
        self.assertEqual(cols[17], 'Average last 6 months')
        self.assertEqual(cols[18], 'Average last 3 months')
        self.assertEqual(cols[19], 'Minimum quantity')
        self.assertEqual(cols[20], 'Maximum quantity')
        for row_number in range(0, rows_len - 1):
            product_name = df.iloc[row_number][0]
            product_categ = df.iloc[row_number][1]
            location_name = df.iloc[row_number][2]
            quantity = df.iloc[row_number][3]
            standard_price = df.iloc[row_number][4]
            price_subtotal = df.iloc[row_number][5]
            description = df.iloc[row_number][6]
            attribute = df.iloc[row_number][7]
            pending_to_send = df.iloc[row_number][8]
            net_stock = df.iloc[row_number][9]
            pending_to_receive = df.iloc[row_number][10]
            stock_provided = df.iloc[row_number][11]
            last_departure = df.iloc[row_number][12]
            last_entry = df.iloc[row_number][13]
            sales_current_month = df.iloc[row_number][14]
            sales_last_month = df.iloc[row_number][15]
            average_12 = df.iloc[row_number][16]
            average_6 = df.iloc[row_number][17]
            average_3 = df.iloc[row_number][18]
            minimum_quantity = df.iloc[row_number][19]
            maximum_quantity = df.iloc[row_number][20]
            if product_name == 'Product test 1':
                self.assertEquals(product_categ, 'All')
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(quantity, 60)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 60 * 90)
                    self.assertEqual(description, 'Description for Product test 1')
                    self.assertEqual(attribute, 'Red;L')
                    self.assertEqual(pending_to_send, 10)
                    self.assertEqual(net_stock, 50)
                    self.assertEqual(pending_to_receive, 15)
                    self.assertEqual(stock_provided, 65)
                    self.assertEqual(
                        last_departure, str(datetime.today().date()))
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 10)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 0.83)
                    self.assertEqual(average_6, 1.67)
                    self.assertEqual(average_3, 3.33)
                    self.assertEqual(minimum_quantity, 10)
                    self.assertEqual(maximum_quantity, 100)
                elif location_name == self.stock_sublocation_1.complete_name:
                    self.assertEqual(quantity, 20)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 20 * 90)
                    self.assertEqual(description, 'Description for Product test 1')
                    self.assertEqual(attribute, 'Red;L')
                    self.assertEqual(pending_to_send, 10)
                    self.assertEqual(net_stock, 10)
                    self.assertEqual(pending_to_receive, 15)
                    self.assertEqual(stock_provided, 25)
                    self.assertEqual(last_departure, '-')
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 10)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 0.83)
                    self.assertEqual(average_6, 1.67)
                    self.assertEqual(average_3, 3.33)
                    self.assertEqual(minimum_quantity, 20)
                    self.assertEqual(maximum_quantity, 200)
                elif location_name == self.stock_sublocation_2.complete_name:
                    self.assertEqual(quantity, 30)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 30 * 90)
                    self.assertEqual(description, 'Description for Product test 1')
                    self.assertEqual(attribute, 'Red;L')
                    self.assertEqual(pending_to_send, 10)
                    self.assertEqual(net_stock, 20)
                    self.assertEqual(pending_to_receive, 15)
                    self.assertEqual(stock_provided, 35)
                    self.assertEqual(last_departure, '-')
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 10)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 0.83)
                    self.assertEqual(average_6, 1.67)
                    self.assertEqual(average_3, 3.33)
                    self.assertEqual(minimum_quantity, 30)
                    self.assertEqual(maximum_quantity, 300)
                elif location_name == self.location_no_parent.complete_name:
                    self.assertEqual(quantity, 18)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 18 * 90)
                    self.assertEqual(description, 'Description for Product test 1')
                    self.assertEqual(attribute, 'Red;L')
                    self.assertEqual(pending_to_send, 10)
                    self.assertEqual(net_stock, 8)
                    self.assertEqual(pending_to_receive, 15)
                    self.assertEqual(stock_provided, 23)
                    self.assertEqual(last_departure, '-')
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 10)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 0.83)
                    self.assertEqual(average_6, 1.67)
                    self.assertEqual(average_3, 3.33)
                    self.assertEqual(minimum_quantity, 40)
                    self.assertEqual(maximum_quantity, 400)
            elif product_name == 'Product test 2':
                self.assertEquals(product_categ, 'All / Categ 1')
                if location_name == self.stock_location.complete_name:
                    self.assertEqual(quantity, 300)
                    self.assertEqual(standard_price, 33)
                    self.assertEqual(price_subtotal, 300 * 33)
                    self.assertEqual(description, '-')
                    self.assertEqual(attribute, 'Red')
                    self.assertEqual(pending_to_send, 15)
                    self.assertEqual(net_stock, 285)
                    self.assertEqual(pending_to_receive, 20)
                    self.assertEqual(stock_provided, 305)
                    self.assertEqual(
                        last_departure, str(datetime.today().date()))
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 15)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 1.25)
                    self.assertEqual(average_6, 2.5)
                    self.assertEqual(average_3, 5)
                    self.assertEqual(minimum_quantity, '-')
                    self.assertEqual(maximum_quantity, '-')
                elif location_name == self.stock_sublocation_1.complete_name:
                    self.assertEqual(quantity, 200)
                    self.assertEqual(standard_price, 33)
                    self.assertEqual(price_subtotal, 200 * 33)
                    self.assertEqual(description, '-')
                    self.assertEqual(attribute, 'Red')
                    self.assertEqual(pending_to_send, 15)
                    self.assertEqual(net_stock, 185)
                    self.assertEqual(pending_to_receive, 20)
                    self.assertEqual(stock_provided, 205)
                    self.assertEqual(last_departure, '-')
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 15)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 1.25)
                    self.assertEqual(average_6, 2.5)
                    self.assertEqual(average_3, 5)
                    self.assertEqual(minimum_quantity, '-')
                    self.assertEqual(maximum_quantity, '-')
                elif location_name == self.location_no_parent.complete_name:
                    self.assertEqual(quantity, 55)
                    self.assertEqual(standard_price, 33)
                    self.assertEqual(price_subtotal, 55 * 33)
                    self.assertEqual(description, '-')
                    self.assertEqual(attribute, 'Red')
                    self.assertEqual(pending_to_send, 15)
                    self.assertEqual(net_stock, 40)
                    self.assertEqual(pending_to_receive, 20)
                    self.assertEqual(stock_provided, 60)
                    self.assertEqual(last_departure, '-')
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 15)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 1.25)
                    self.assertEqual(average_6, 2.5)
                    self.assertEqual(average_3, 5)
                    self.assertEqual(minimum_quantity, '-')
                    self.assertEqual(maximum_quantity, '-')
        total = df.iloc[rows_len - 1][cols_len - 16]
        self.assertGreater(total, 0)

    def test_export_stock_inventory_valued_specific_date(self):
        self.update_qty_on_hand(self.product_1, self.stock_location, 10)
        self.update_qty_on_hand(self.product_1, self.stock_sublocation_1, 20)
        self.update_qty_on_hand(self.product_1, self.stock_sublocation_2, 30)
        self.update_qty_on_hand(self.product_1, self.location_no_parent, 1)
        self.create_sale_order(self.product_1, 5)
        self.create_purchase_order(self.product_1, 10)
        moves = self.env['stock.move'].search([
            ('product_id', '=', self.product_1.id),
            ('product_uom_qty', '=', 10),
            ('location_dest_id', '=', self.stock_location.id),
        ])
        self.assertEqual(len(moves), 2)
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
        self.assertEqual(cols_len, 21)
        self.assertEqual(cols[0], 'Product')
        self.assertEqual(cols[1], 'Product category')
        self.assertEqual(cols[2], 'Location')
        self.assertEqual(cols[3], 'Quantity')
        self.assertEqual(cols[4], 'Standard price')
        self.assertEqual(cols[5], 'Subtotal')
        self.assertEqual(cols[6], 'Description')
        self.assertEqual(cols[7], 'Attribute')
        self.assertEqual(cols[8], 'Pending to send')
        self.assertEqual(cols[9], 'Net stock')
        self.assertEqual(cols[10], 'Pending to receive')
        self.assertEqual(cols[11], 'Stock provided')
        self.assertEqual(cols[12], 'Last departure')
        self.assertEqual(cols[13], 'Last entry')
        self.assertEqual(cols[14], 'Sales current month')
        self.assertEqual(cols[15], 'Sales last month')
        self.assertEqual(cols[16], 'Average last 12 months')
        self.assertEqual(cols[17], 'Average last 6 months')
        self.assertEqual(cols[18], 'Average last 3 months')
        self.assertEqual(cols[19], 'Minimum quantity')
        self.assertEqual(cols[20], 'Maximum quantity')
        for row_number in range(0, rows_len - 1):
            product_name = df.iloc[row_number][0]
            product_categ = df.iloc[row_number][1]
            location_name = df.iloc[row_number][2]
            quantity = df.iloc[row_number][3]
            standard_price = df.iloc[row_number][4]
            price_subtotal = df.iloc[row_number][5]
            description = df.iloc[row_number][6]
            attribute = df.iloc[row_number][7]
            pending_to_send = df.iloc[row_number][8]
            net_stock = df.iloc[row_number][9]
            pending_to_receive = df.iloc[row_number][10]
            stock_provided = df.iloc[row_number][11]
            last_departure = df.iloc[row_number][12]
            last_entry = df.iloc[row_number][13]
            sales_current_month = df.iloc[row_number][14]
            sales_last_month = df.iloc[row_number][15]
            average_12 = df.iloc[row_number][16]
            average_6 = df.iloc[row_number][17]
            average_3 = df.iloc[row_number][18]
            minimum_quantity = df.iloc[row_number][19]
            maximum_quantity = df.iloc[row_number][20]
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
                    self.assertEqual(
                        description, 'Description for Product test 1')
                    self.assertEqual(attribute, 'Red;L')
                    self.assertEqual(pending_to_send, 5)
                    self.assertEqual(net_stock, 5)
                    self.assertEqual(pending_to_receive, 10)
                    self.assertEqual(stock_provided, 15)
                    self.assertEqual(last_departure,
                                     str(datetime.today().date()))
                    self.assertEqual(last_entry, str(datetime.today().date()))
                    self.assertEqual(sales_current_month, 5)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 0.42)
                    self.assertEqual(average_6, 0.83)
                    self.assertEqual(average_3, 1.67)
                    self.assertEqual(minimum_quantity, 10)
                    self.assertEqual(maximum_quantity, 100)
                elif location_name == self.location_no_parent.complete_name:
                    self.assertEqual(quantity, 1)
                    self.assertEqual(standard_price, 90)
                    self.assertEqual(price_subtotal, 1 * 90)
                    self.assertEqual(
                        description, 'Description for Product test 1')
                    self.assertEqual(attribute, 'Red;L')
                    self.assertEqual(pending_to_send, 5)
                    self.assertEqual(net_stock, -4)
                    self.assertEqual(pending_to_receive, 10)
                    self.assertEqual(stock_provided, 6)
                    self.assertEqual(last_departure, '-')
                    self.assertEqual(
                        last_entry,
                        str(datetime.today().date() - timedelta(15)))
                    self.assertEqual(sales_current_month, 5)
                    self.assertEqual(sales_last_month, 0)
                    self.assertEqual(average_12, 0.42)
                    self.assertEqual(average_6, 0.83)
                    self.assertEqual(average_3, 1.67)
                    self.assertEqual(minimum_quantity, 40)
                    self.assertEqual(maximum_quantity, 400)
        total = df.iloc[rows_len - 2][cols_len - 16]
        self.assertGreater(total, 0)
