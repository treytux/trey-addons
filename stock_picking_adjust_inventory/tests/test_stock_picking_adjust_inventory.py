###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPickingAdjustInventory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref(
            'product.product_product_3_product_template').product_variant_id
        self.location = self.env.ref('stock.stock_location_stock')
        self.location_dest = self.env.ref('stock.location_dispatch_zone')

    def inventory(self, location, qty):
        inventory = self.env['stock.inventory'].create({
            'name': 'add products for tests',
            'filter': 'product',
            'location_id': location.id,
            'product_id': self.product.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.write({
            'product_qty': qty,
            'location_id': location.id,
        })
        inventory._action_done()

    def test_adjust_complete(self):
        self.inventory(self.location, 0)
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_dest_id': self.location_dest.id,
            'location_id': self.location.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_lines': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                    'product_uom': self.product.uom_id.id,
                    'location_dest_id': self.location_dest.id,
                    'location_id': self.location.id,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id,
                }),
            ],
        })
        inventory_obj = self.env['stock.move.adjust_inventory'].with_context(
            active_model='stock.move',
            active_id=picking.move_lines[0].id,
        )
        wizard = inventory_obj.create({})
        self.assertEquals(wizard.quantity, 10)
        product = wizard.product_id.with_context(
            location=wizard.location_id.id)
        self.assertEquals(product.qty_available, 0)
        wizard.action_adjust()
        product = wizard.product_id.with_context(
            location=wizard.location_id.id)
        self.assertEquals(product.qty_available, 10)

    def test_adjust_with_reserved(self):
        self.inventory(self.location, 4)
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_dest_id': self.location_dest.id,
            'location_id': self.location.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_lines': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                    'product_uom': self.product.uom_id.id,
                    'location_dest_id': self.location_dest.id,
                    'location_id': self.location.id,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id,
                }),
            ],
        })
        move = picking.move_lines[0]
        self.assertEquals(move.product_uom_qty, 10)
        self.assertEquals(move.reserved_availability, 0)
        picking.action_assign()
        self.assertEquals(move.product_uom_qty, 10)
        self.assertEquals(move.reserved_availability, 4)
        inventory_obj = self.env['stock.move.adjust_inventory'].with_context(
            active_model='stock.move',
            active_id=picking.move_lines[0].id,
        )
        wizard = inventory_obj.create({})
        self.assertEquals(wizard.quantity, 6)
        product = wizard.product_id.with_context(
            location=wizard.location_id.id)
        self.assertEquals(product.qty_available, 4)
        wizard.action_adjust()
        product = wizard.product_id.with_context(
            location=wizard.location_id.id)
        self.assertEquals(product.qty_available, 10)
