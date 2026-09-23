###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockMoveTreePrice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        location = self.env.ref('stock.stock_location_customers')
        inventory = self.env['stock.inventory'].create({
            'name': 'Test inventory',
            'location_id': location.id,
            'filter': 'partial'
        })
        inventory.action_start()
        self.env['stock.inventory.line'].create({
            'inventory_id': inventory.id,
            'product_id': self.product.id,
            'location_id': location.id,
            'product_qty': 100,
        })
        inventory._action_done()

    def test_sale_price(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'discount': 10,
                'taxes_id': [(6, 0, [])],
            })],
        })
        sale.action_confirm()
        line = sale.order_line
        self.assertEquals(line.price_unit, 100)
        self.assertEquals(line.discount, 10)
        self.assertEquals(line.price_subtotal, 180)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.action_done()
        self.assertEquals(len(picking.move_lines), 1)
        move = picking.move_lines
        self.assertEquals(move.product_uom_qty, 2)
        self.assertEquals(move.sale_price_unit, 100)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 180)
        sale.order_line[0].price_unit = 200
        self.assertEquals(move.product_uom_qty, 2)
        self.assertEquals(move.sale_price_unit, 200)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 360)

    def test_sale_price_validate_less_qty(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'discount': 10,
                'taxes_id': [(6, 0, [])],
            })],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        move = picking.move_lines
        self.assertEquals(move.product_uom_qty, 2)
        self.assertEquals(move.sale_price_unit, 100)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 180)
        picking.move_lines[0].quantity_done = 1
        picking.action_done()
        self.assertEquals(move.product_uom_qty, 1)
        self.assertEquals(move.sale_price_unit, 100)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 90)
        sale.order_line[0].price_unit = 200
        self.assertEquals(move.product_uom_qty, 1)
        self.assertEquals(move.sale_price_unit, 200)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 180)

    def test_sale_price_validate_more_qty(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'discount': 10,
                'taxes_id': [(6, 0, [])],
            })],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        move = picking.move_lines
        self.assertEquals(move.product_uom_qty, 2)
        self.assertEquals(move.sale_price_unit, 100)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 180)
        picking.move_lines[0].quantity_done = 3
        picking.action_done()
        self.assertEquals(move.product_uom_qty, 3)
        self.assertEquals(move.sale_price_unit, 100)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 270)
        sale.order_line[0].price_unit = 200
        self.assertEquals(move.product_uom_qty, 3)
        self.assertEquals(move.sale_price_unit, 200)
        self.assertEquals(move.sale_discount, 10)
        self.assertEquals(move.sale_subtotal, 540)

    def test_purchase_price_less_qty(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': self.product.standard_price,
                    'discount': 10,
                    'product_qty': 2,
                    'date_planned': fields.Date.today(),
                    'taxes_id': [(6, 0, [])],
                })],
        })
        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        move = picking.move_lines
        picking.action_confirm()
        picking.action_assign()
        move = picking.move_lines
        self.assertEquals(move.product_uom_qty, 2)
        self.assertEquals(move.purchase_price_unit, 10)
        self.assertEquals(move.purchase_discount, 10)
        self.assertEquals(move.purchase_subtotal, 18)
        picking.move_lines[0].quantity_done = 1
        picking.action_done()
        self.assertEquals(move.product_uom_qty, 1)
        self.assertEquals(move.purchase_price_unit, 10)
        self.assertEquals(move.purchase_discount, 10)
        self.assertEquals(move.purchase_subtotal, 9)
        purchase.order_line[0].price_unit = 20
        self.assertEquals(move.product_uom_qty, 1)
        self.assertEquals(move.purchase_price_unit, 20)
        self.assertEquals(move.purchase_discount, 10)
        self.assertEquals(move.purchase_subtotal, 18)

    def test_purchase_price_more_qty(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': self.product.standard_price,
                    'discount': 10,
                    'product_qty': 2,
                    'date_planned': fields.Date.today(),
                    'taxes_id': [(6, 0, [])],
                })],
        })
        purchase.button_confirm()
        picking = purchase.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        move = picking.move_lines
        picking.action_confirm()
        picking.action_assign()
        move = picking.move_lines
        self.assertEquals(move.product_uom_qty, 2)
        self.assertEquals(move.purchase_price_unit, 10)
        self.assertEquals(move.purchase_discount, 10)
        self.assertEquals(move.purchase_subtotal, 18)
        picking.move_lines[0].quantity_done = 3
        picking.action_done()
        self.assertEquals(move.product_uom_qty, 3)
        self.assertEquals(move.purchase_price_unit, 10)
        self.assertEquals(move.purchase_discount, 10)
        self.assertEquals(move.purchase_subtotal, 27)
        purchase.order_line[0].price_unit = 20
        self.assertEquals(move.product_uom_qty, 3)
        self.assertEquals(move.purchase_price_unit, 20)
        self.assertEquals(move.purchase_discount, 10)
        self.assertEquals(move.purchase_subtotal, 54)
