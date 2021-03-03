###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPurchaseReport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'property_cost_method': 'fifo',
            'company_id': False,
            'name': 'Product',
            'standard_price': 10,
            'list_price': 100,
        })

    def create_purchase(self, quantity, price_unit):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': self.product.id,
        })
        line.onchange_product_id()
        line.update({
            'price_unit': price_unit,
            'product_qty': quantity,
        })
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        return purchase

    def create_sale(self, quantity):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': quantity,
                    'price_unit': 100,
                })
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        return sale

    def test_value_inventory(self):
        purchase = self.create_purchase(1, 10)
        move_1 = purchase.picking_ids.move_lines
        self.assertEquals(move_1.price_unit, 10)
        self.assertEquals(move_1.remaining_qty, 1)
        self.assertEquals(move_1.remaining_value, 10)
        purchase = self.create_purchase(4, 5)
        move_2 = purchase.picking_ids.move_lines
        self.assertEquals(move_2.price_unit, 5)
        self.assertEquals(move_2.remaining_qty, 4)
        self.assertEquals(move_2.remaining_value, 20)
        self.create_sale(2)
        self.assertEquals(move_1.remaining_qty, 0)
        self.assertEquals(move_2.remaining_qty, 3)
        self.create_sale(2)
        self.assertEquals(move_1.remaining_qty, 0)
        self.assertEquals(move_2.remaining_qty, 1)
        purchase = self.create_purchase(1, 100)
        move_3 = purchase.picking_ids.move_lines
        self.assertEquals(move_1.remaining_qty, 0)
        self.assertEquals(move_2.remaining_qty, 1)
        self.assertEquals(move_3.remaining_qty, 1)
        inventory = self.env['stock.inventory'].create({
            'name': 'add products for tests',
            'filter': 'product',
            'location_id': move_1.location_dest_id.id,
            'product_id': self.product.id,
            'exhausted': True})
        inventory.action_start()
        inventory.line_ids.write({
            'product_qty': 10,
            'location_id': move_1.location_dest_id.id})
        inventory._action_done()
        move_inv = inventory.move_ids
        self.assertEquals(move_inv.price_unit, 5)
        self.assertEquals(move_inv.remaining_qty, 8)
        self.assertEquals(move_inv.remaining_value, 40)
