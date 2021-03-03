###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestPurchaseOrderRepair(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'supplier': True,
        })
        self.product1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.picking_type_in_id = self.ref('stock.picking_type_in')
        self.picking_type_in_repair_id = self.ref(
            'purchase_order_repair.stock_picking_type_in_repair')
        self.picking_type_out_repair_id = self.ref(
            'purchase_order_repair.stock_picking_type_out_repair')
        picking_type_in_repair = self.env['stock.picking.type'].browse(
            self.picking_type_in_repair_id)
        self.assertTrue(picking_type_in_repair.auto_return_picking)

    def create_purchase(self, picking_type_id=None):
        data = {
            'partner_id': self.supplier.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product1.id,
                    'name': self.product1.name,
                    'product_qty': 1.0,
                    'product_uom': self.product1.uom_id.id,
                    'price_unit': self.product1.standard_price,
                    'date_planned': fields.Date.today(),
                }),
            ]
        }
        if picking_type_id:
            data.update({
                'picking_type_id': picking_type_id,
            })
        return self.env['purchase.order'].create(data)

    def test_po_common(self):
        purchase = self.create_purchase()
        self.assertEquals(purchase.state, 'draft')
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.assertEquals(len(purchase.picking_ids), 1)
        self.assertEquals(
            purchase.picking_ids.picking_type_id.id, self.picking_type_in_id)

    def test_po_repair(self):
        purchase = self.create_purchase(
            picking_type_id=self.picking_type_in_repair_id)
        self.assertTrue(purchase.amount_total > 0)
        self.assertEquals(purchase.state, 'draft')
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.assertEquals(len(purchase.picking_ids), 2)
        picking_out = purchase.picking_ids[0]
        self.assertEquals(
            picking_out.picking_type_id.id, self.picking_type_out_repair_id)
        self.assertEquals(picking_out.state, 'assigned')
        picking_in = purchase.picking_ids[1]
        self.assertEquals(
            picking_in.picking_type_id.id, self.picking_type_in_repair_id)
        self.assertEquals(picking_in.state, 'waiting')
        picking_out.move_lines.quantity_done = 1
        picking_out.action_done()
        self.assertEquals(picking_out.state, 'done')
        self.assertEquals(picking_in.state, 'assigned')
        picking_in.move_lines.quantity_done = 1
        picking_in.action_done()
        self.assertEquals(picking_in.state, 'done')
