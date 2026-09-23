###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import time
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase


class TestsProductPurchaseLastPrice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Test Supplier',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.env.user.company_id.id,
            'name': 'Test product 1',
            'standard_price': 70,
            'list_price': 130,
            'seller_ids': [(0, 0, {
                'partner_id': self.supplier_01.id,
                'product_code': 'TEST_PRODUCT_01',
                'price': 80,
            })],
        })

    def create_purchase(self):
        return self.env['purchase.order'].create({
            'partner_id': self.supplier_01.id,
        })

    def create_sale_order(self, partner, qty):
        order_line = {
            'name': self.product_01.name,
            'product_id': self.product_01.id,
            'product_uom_qty': qty,
            'product_uom': self.product_01.uom_id.id,
            'price_unit': self.product_01.list_price,
        }
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, order_line)],
        })

    def create_purchase_line(self, purchase, product, price=False, discount=False):
        line_obj = self.env['purchase.order.line']
        if discount:
            product.seller_ids.filtered(
                lambda seller: seller.partner_id == purchase.partner_id
            ).discount = discount
        line = line_obj.new({
            'order_id': purchase.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        data = {
            'product_qty': 2,
        }
        if price:
            data.update({
                'price_unit': price,
            })
        if discount:
            data.update({
                'discount': discount,
            })
        line.write(data)
        return line

    def test_template_with_multiple_variants_purchase_last_price(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Size',
        })
        size_s = self.env['product.attribute.value'].create({
            'name': 'S',
            'attribute_id': attribute.id,
        })
        size_m = self.env['product.attribute.value'].create({
            'name': 'M',
            'attribute_id': attribute.id,
        })
        template = self.env['product.template'].create({
            'name': 'Product with variants',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attribute.id,
                'value_ids': [(6, 0, [size_s.id, size_m.id])],
            })],
        })
        self.assertEqual(len(template.product_variant_ids), 2)
        self.assertEqual(template.purchase_last_price, 0.0)
        self.assertEqual(template.margin_purchase_last_price, 0.0)

    def test_purchase_last_price(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product_01)
        self.assertEqual(purchase.order_line.price_unit, 80)
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.write({
            'qty_done': 2,
        })
        self.assertEqual(self.product_01.purchase_last_price, 0.0)
        self.assertEqual(self.product_01.margin_purchase_last_price, 0.0)
        picking.button_validate()
        self.assertEqual(self.product_01.purchase_last_price, 80)
        self.assertEqual(self.product_01.margin_purchase_last_price, 38.46)

    def test_purchase_last_price_force_price(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product_01, 100)
        self.assertEqual(purchase.order_line.price_unit, 100)
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.write({
            'qty_done': 2,
        })
        self.assertEqual(self.product_01.purchase_last_price, 0.0)
        self.assertEqual(self.product_01.margin_purchase_last_price, 0.0)
        picking.button_validate()
        self.assertEqual(self.product_01.purchase_last_price, 100)
        self.assertEqual(self.product_01.margin_purchase_last_price, 23.08)

    def test_purchase_last_price_calculate_in_product(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product_01)
        self.assertEqual(purchase.order_line.price_unit, 80)
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.write({
            'qty_done': 2,
        })
        self.assertEqual(self.product_01.purchase_last_price, 0.0)
        self.assertEqual(self.product_01.margin_purchase_last_price, 0.0)
        picking.button_validate()
        self.assertEqual(self.product_01.purchase_last_price, 80)
        self.product_01.purchase_last_price = 0.0
        self.product_01.calculate_purchase_last_price()
        self.assertEqual(self.product_01.purchase_last_price, 80)
        self.assertEqual(self.product_01.margin_purchase_last_price, 38.46)

    def test_purchase_last_price_with_discount(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product_01, discount=50)
        self.assertEqual(purchase.order_line.price_unit, 80)
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.write({
            'qty_done': 2,
        })
        self.assertEqual(self.product_01.purchase_last_price, 0.0)
        self.assertEqual(self.product_01.margin_purchase_last_price, 0.0)
        picking.button_validate()
        self.assertEqual(self.product_01.purchase_last_price, 40)
        self.assertEqual(self.product_01.margin_purchase_last_price, 69.23)

    def test_purchase_last_price_force_price_with_discount(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product_01, 100, discount=50)
        self.assertEqual(purchase.order_line.price_unit, 100)
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.write({
            'qty_done': 2,
        })
        self.assertEqual(self.product_01.purchase_last_price, 0.0)
        self.assertEqual(self.product_01.margin_purchase_last_price, 0.0)
        picking.button_validate()
        self.assertEqual(self.product_01.purchase_last_price, 50)
        self.assertEqual(self.product_01.margin_purchase_last_price, 61.54)

    def test_purchase_last_price_calculate_in_product_with_discount(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product_01, discount=50)
        self.assertEqual(purchase.order_line.price_unit, 80)
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.write({
            'qty_done': 2,
        })
        self.assertEqual(self.product_01.purchase_last_price, 0.0)
        self.assertEqual(self.product_01.margin_purchase_last_price, 0.0)
        picking.button_validate()
        self.assertEqual(self.product_01.purchase_last_price, 40)
        self.product_01.purchase_last_price = 0.0
        self.product_01.calculate_purchase_last_price()
        self.assertEqual(self.product_01.purchase_last_price, 40)
        self.assertEqual(self.product_01.margin_purchase_last_price, 69.23)

    def test_update_price_in_po_where_another_picking_in_was_validate(self):
        sale_01 = self.create_sale_order(self.supplier_01, 2)
        sale_01.action_confirm()
        picking_sale_01 = sale_01.picking_ids
        picking_sale_01.action_assign()
        self.assertEqual(sale_01.order_line.purchase_last_price, 0.0)
        self.assertNotEqual(picking_sale_01.move_ids.state, 'done')
        purchase_01 = self.create_purchase()
        self.create_purchase_line(purchase_01, self.product_01, 100)
        purchase_01.button_confirm()
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_assign()
        picking_in_01.move_line_ids.write({
            'qty_done': 2,
        })
        picking_in_01.button_validate()
        self.assertEqual(sale_01.order_line.purchase_last_price, 100)
        picking_sale_01.action_assign()
        picking_sale_01.move_line_ids.write({
            'qty_done': 2,
        })
        picking_sale_01.with_context(force_button_validate=True).button_validate()
        self.assertEqual(picking_sale_01.move_ids.state, 'done')
        self.assertEqual(sale_01.order_line.purchase_last_price, 100)
        report_line = self.env['sale.report.from_stock_move'].search([
            ('order_id', '=', sale_01.id),
        ], limit=1)
        self.assertEqual(report_line.purchase_last_price, 200)
        purchase_02 = self.create_purchase()
        self.create_purchase_line(purchase_02, self.product_01, 150)
        purchase_02.button_confirm()
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_assign()
        picking_in_02.move_line_ids.write({
            'qty_done': 2,
        })
        picking_in_02.button_validate()
        picking_in_02.move_ids.date = fields.Datetime.to_string(
            fields.Datetime.from_string(picking_in_01.move_line_ids.date)
            + timedelta(minutes=1))
        self.assertEqual(sale_01.order_line.purchase_last_price, 100)
        self.assertEqual(self.product_01.purchase_last_price, 150)
        purchase_01.order_line.write({
            'price_unit': 80,
        })
        self.assertEqual(sale_01.order_line.purchase_last_price, 80)
        self.assertEqual(self.product_01.purchase_last_price, 150)

    def test_update_price_in_po_where_another_picking_in_was_validate_with_discount(
            self):
        sale_01 = self.create_sale_order(self.supplier_01, 2)
        sale_01.action_confirm()
        picking_sale_01 = sale_01.picking_ids
        picking_sale_01.action_assign()
        self.assertEqual(sale_01.order_line.purchase_last_price, 0.0)
        self.assertNotEqual(picking_sale_01.move_ids.state, 'done')
        purchase_01 = self.create_purchase()
        self.create_purchase_line(purchase_01, self.product_01, 100, discount=50)
        purchase_01.button_confirm()
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_assign()
        picking_in_01.move_line_ids.write({
            'qty_done': 2,
        })
        picking_in_01.button_validate()
        self.assertEqual(sale_01.order_line.purchase_last_price, 50)
        picking_sale_01.action_assign()
        picking_sale_01.move_line_ids.write({
            'qty_done': 2,
        })
        picking_sale_01.with_context(force_button_validate=True).button_validate()
        self.assertEqual(picking_sale_01.move_ids.state, 'done')
        self.assertEqual(sale_01.order_line.purchase_last_price, 50)
        purchase_02 = self.create_purchase()
        self.create_purchase_line(purchase_02, self.product_01, 150, discount=50)
        purchase_02.button_confirm()
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_assign()
        picking_in_02.move_line_ids.write({
            'qty_done': 2,
        })
        time.sleep(1)
        picking_in_02.button_validate()
        picking_in_02.move_ids.date = fields.Datetime.to_string(
            fields.Datetime.from_string(picking_in_01.move_line_ids.date)
            + timedelta(minutes=1))
        self.assertEqual(sale_01.order_line.purchase_last_price, 50)
        self.assertEqual(self.product_01.purchase_last_price, 75)
        purchase_01.order_line.write({
            'price_unit': 80,
        })
        self.assertEqual(sale_01.order_line.purchase_last_price, 40)
        self.assertEqual(self.product_01.purchase_last_price, 75)

    def test_write_purchase_last_price_and_recalculate(self):
        sale_01 = self.create_sale_order(self.supplier_01, 2)
        sale_01.action_confirm()
        picking_sale_01 = sale_01.picking_ids
        picking_sale_01.action_assign()
        self.assertEqual(sale_01.order_line.purchase_last_price, 0.0)
        self.assertNotEqual(picking_sale_01.move_ids.state, 'done')
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product_01, 100)
        purchase.button_confirm()
        picking_in = purchase.picking_ids
        picking_in.action_assign()
        picking_in.move_line_ids.write({
            'qty_done': 2,
        })
        picking_in.button_validate()
        self.assertEqual(sale_01.order_line.purchase_last_price, 100)
        picking_sale_01.action_assign()
        picking_sale_01.move_line_ids.write({
            'qty_done': 2,
        })
        picking_sale_01.with_context(force_button_validate=True).button_validate()
        self.assertEqual(picking_sale_01.move_ids.state, 'done')
        self.assertEqual(sale_01.order_line.purchase_last_price, 100)
        purchase.order_line.write({
            'price_unit': 80,
        })
        self.assertEqual(sale_01.order_line.purchase_last_price, 80)
        self.assertEqual(self.product_01.purchase_last_price, 80)
        sale_01.order_line.write({
            'purchase_last_price': 50,
        })
        self.assertEqual(sale_01.order_line.purchase_last_price, 50)
        sale_01.order_line.recalculate_purchase_last_price()
        self.assertEqual(sale_01.order_line.purchase_last_price, 80)

    def test_two_move_ids_in_one_sale_order_line_write_and_calculate(self):
        sale_01 = self.create_sale_order(self.supplier_01, 4)
        sale_01.action_confirm()
        picking_sale_01 = sale_01.picking_ids
        picking_sale_01.action_assign()
        self.assertEqual(sale_01.order_line.purchase_last_price, 0.0)
        self.assertNotEqual(picking_sale_01.move_ids.state, 'done')
        purchase_01 = self.create_purchase()
        self.create_purchase_line(purchase_01, self.product_01, 100)
        purchase_01.button_confirm()
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_assign()
        picking_in_01.move_line_ids.write({
            'qty_done': 2,
        })
        picking_in_01.button_validate()
        purchase_02 = self.create_purchase()
        self.create_purchase_line(purchase_02, self.product_01, 125)
        purchase_02.button_confirm()
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_assign()
        picking_in_02.move_line_ids.write({
            'qty_done': 2,
        })
        picking_in_02.button_validate()
        picking_in_02.move_ids.date = fields.Datetime.to_string(
            fields.Datetime.from_string(picking_in_01.move_line_ids.date)
            + timedelta(minutes=1))
        picking_sale_01.action_assign()
        self.assertEqual(picking_sale_01.move_ids.product_uom_qty, 4)
        picking_sale_01.move_line_ids.write({
            'qty_done': 2,
        })
        self.assertEqual(len(sale_01.picking_ids), 1)
        res = picking_sale_01.button_validate()
        self.env['stock.backorder.confirmation'].with_context(
            res['context']).create({}).process()
        picking_sale_01.move_ids.write({
            'date': fields.Datetime.to_string(
                fields.Datetime.from_string(picking_in_01.move_line_ids.date)
                + timedelta(minutes=2))
        })
        self.assertEqual(picking_sale_01.move_ids.state, 'done')
        self.assertEqual(len(sale_01.picking_ids), 2)
        picking_sale_02 = sale_01.picking_ids.filtered(lambda p: p != picking_sale_01)
        self.assertEqual(picking_sale_01.move_ids.state, 'done')
        self.assertEqual(sale_01.order_line.purchase_last_price, 125)
        picking_sale_02.action_assign()
        self.assertEqual(picking_sale_01.move_ids.product_uom_qty, 2)
        picking_sale_02.move_line_ids.write({
            'qty_done': 2,
        })
        picking_sale_02.with_context(force_button_validate=True).button_validate()
        picking_sale_02.move_ids.write({
            'date': fields.Datetime.to_string(
                fields.Datetime.from_string(picking_in_02.move_line_ids.date)
                + timedelta(minutes=2))
        })
        self.assertEqual(picking_sale_02.move_ids.state, 'done')
        self.assertEqual(sale_01.order_line.purchase_last_price, 125)
        purchase_01.order_line.write({
            'price_unit': 80,
        })
        self.assertEqual(sale_01.order_line.purchase_last_price, 125)
        self.assertEqual(self.product_01.purchase_last_price, 125)
        purchase_02.order_line.write({
            'price_unit': 110,
        })
        self.assertEqual(sale_01.order_line.purchase_last_price, 110)
        self.assertEqual(self.product_01.purchase_last_price, 110)
        sale_01.order_line.purchase_last_price = 0
        self.assertEqual(sale_01.order_line.purchase_last_price, 0)
        sale_01.order_line.recalculate_purchase_last_price()
        self.assertEqual(sale_01.order_line.purchase_last_price, 110)
