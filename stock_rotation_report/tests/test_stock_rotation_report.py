###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from calendar import monthrange
from datetime import date

from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockRotationReport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.user.company_id
        self.company.is_stock_rotation = True
        self.partner = self.env['res.partner'].create({
            'name': 'Partner Supplier / Customer test',
            'customer': True,
            'supplier': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'weight': 10,
        })
        self.today = fields.Date.today()
        self.days_of_month = monthrange(
            self.today.year, self.today.month)[1]
        self.company.rotation_init_date = date(
            self.today.year, self.today.month, 1)
        self.date_init = date(
            self.today.year, self.today.month, 1)
        self.date_end = date(
            self.today.year, self.today.month, self.days_of_month)

    def create_purchase(self):
        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_qty': 100,
                'price_unit': 50,
                'date_planned': fields.Date.today(),
            })]
        })
        order.button_confirm()
        return order

    def create_sale(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 50,
                'price_unit': 100,
            })]
        })
        order.action_confirm()
        return order

    def confirm_picking(self, order):
        picking = order.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def create_inventory(self):
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'Period inventory test',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
            'date': fields.Date.today(),
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': self.product.id,
            'product_qty': 51,
            'location_id': location.id,
        })
        inventory._action_done()
        return inventory

    def test_stock_rotation(self):
        rotation = self.env['product.product.stock.rotation']
        inventory_order = self.create_inventory()
        purchase_order = self.create_purchase()
        self.confirm_picking(order=purchase_order)
        self.assertEqual(purchase_order.picking_ids[0].state, 'done')
        sale_order = self.create_sale()
        self.confirm_picking(order=sale_order)
        self.assertEqual(sale_order.picking_ids[0].state, 'done')
        self.assertEqual(inventory_order.state, 'done')
        self.assertEqual(self.product.qty_available, 101)
        rotation.compute_stock_rotation_day(
            init_date=self.date_init, end_date=self.date_end,
            company=self.company)
        product_rotation = rotation.search([
            ('product_id', '=', self.product.id),
            ('qty_inventory', '!=', 0.00)], limit=1)
        self.assertEqual(product_rotation.qty_inventory, 51)
