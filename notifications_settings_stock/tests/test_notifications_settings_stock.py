###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestNotificationsSettingsStock(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'product',
            'list_price': 10,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10,
            })]
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        website = self.env['website'].create({
            'name': 'new website',
        })
        self.sale.website_id = website

    def test_notify_stock_picking_confirm_assign(self):
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.website_id.notify_stock_assigned = True
        picking.website_id.notify_stock_confirmed = True
        quantity = 20.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.stock_location, quantity)
        message_ids_tam = len(picking.message_ids)
        picking.action_confirm()
        picking.action_assign()
        last_message = picking.message_ids[0]
        self.assertIn('is ready to be shipped.', last_message.body)
        last_message = picking.message_ids[2]
        self.assertIn('is been prepared.', last_message.body)
        self.assertNotEqual(message_ids_tam, len(picking.message_ids))
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        last_message = picking.message_ids[0]
        self.assertNotIn('will leave our plant shortly.', last_message.body)

    def test_notify_stock_picking_cancel(self):
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.website_id.notify_stock_cancel = True
        quantity = 20.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.stock_location, quantity)
        picking.action_confirm()
        picking.action_assign()
        for message in picking.message_ids:
            self.assertNotIn('is been prepared.', message.body)
            self.assertNotIn('is ready to be shipped.', message.body)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        message_ids_tam = len(picking.message_ids)
        picking.action_cancel()
        last_message = picking.message_ids[0]
        self.assertIn('has been canceled.', last_message.body)
        self.assertNotEqual(message_ids_tam, len(picking.message_ids))

    def test_notify_stock_picking_done(self):
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.website_id.notify_stock_done = True
        quantity = 20.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.stock_location, quantity)
        picking.action_confirm()
        picking.action_assign()
        for message in picking.message_ids:
            self.assertNotIn('is been prepared.', message.body)
            self.assertNotIn('is ready to be shipped.', message.body)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        message_ids_tam = len(picking.message_ids)
        picking.action_done()
        last_message = picking.message_ids[0]
        self.assertIn('will leave our plant shortly.', last_message.body)
        self.assertNotEqual(message_ids_tam, len(picking.message_ids))
