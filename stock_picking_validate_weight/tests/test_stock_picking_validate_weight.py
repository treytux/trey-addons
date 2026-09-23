###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPickingValidateWeight(TransactionCase):

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
            'weight': 10,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Inventory test',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        self.inventory.line_ids.create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'product_qty': 100,
            'location_id': self.location.id,
        })
        self.inventory.action_start()
        self.inventory._action_done()
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 20,
            })],
        })

    def test_wizard_01(self):
        self.assertEquals(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(picking.weight, 200)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(picking.state, 'assigned')
        self.assertEquals(len(picking.move_lines), 1)
        wizard = self.env['stock.immediate.transfer'].create(
            {'pick_ids': [(4, picking.id)]})
        self.assertEquals(wizard.weight, 200)
        wizard.weight = 10
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(picking.shipping_weight, 10)
        self.assertEquals(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_02(self):
        self.assertEquals(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(picking.weight, 200)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(picking.state, 'assigned')
        self.assertEquals(len(picking.move_lines), 1)
        picking.move_lines[0].quantity_done = 10
        self.assertEquals(picking.move_lines[0].quantity_done, 10)
        wizard = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(4, picking.id)],
        })
        self.assertEquals(wizard.weight, 100)
        wizard.weight = 15
        self.assertEquals(wizard.weight, 15)
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(picking.shipping_weight, 15)
        self.assertEquals(len(self.sale.picking_ids), 2)
        self.assertEquals(self.sale.picking_ids[1].weight, 100)
        self.assertEquals(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_03(self):
        self.assertEquals(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(picking.weight, 200)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(picking.state, 'assigned')
        self.assertEquals(len(picking.move_lines), 1)
        picking.move_lines[0].quantity_done = 10
        self.assertEquals(picking.move_lines[0].quantity_done, 10)
        wizard = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(4, picking.id)],
        })
        self.assertEquals(wizard.weight, 100)
        wizard.weight = 15
        self.assertEquals(wizard.weight, 15)
        wizard.process_cancel_backorder()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(picking.shipping_weight, 15)
        self.assertEquals(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_04(self):
        self.assertEquals(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(picking.weight, 200)
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.carrier_id)
        free_delivery = self.env.ref('delivery.free_delivery_carrier')
        picking.carrier_id = free_delivery.id
        self.assertEquals(picking.carrier_id, free_delivery)
        wizard = self.env['stock.immediate.transfer'].create(
            {'pick_ids': [(4, picking.id)]})
        self.assertEquals(wizard.weight, 200)
        wizard.weight = 10
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(picking.shipping_weight, 10)
        self.assertEquals(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_05(self):
        self.assertEquals(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(picking.weight, 200)
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.carrier_id)
        free_delivery = self.env.ref('delivery.free_delivery_carrier')
        picking.carrier_id = free_delivery.id
        self.assertEquals(picking.carrier_id, free_delivery)
        self.assertEquals(picking.state, 'assigned')
        self.assertEquals(len(picking.move_lines), 1)
        picking.move_lines[0].quantity_done = 10
        self.assertEquals(picking.move_lines[0].quantity_done, 10)
        wizard = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(4, picking.id)],
        })
        self.assertEquals(wizard.weight, 100)
        wizard.weight = 15
        self.assertEquals(wizard.weight, 15)
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(picking.shipping_weight, 15)
        self.assertEquals(len(self.sale.picking_ids), 2)
        self.assertEquals(self.sale.picking_ids[1].weight, 100)
        self.assertEquals(
            picking.shipping_weight, picking.shipping_weight_validate)
