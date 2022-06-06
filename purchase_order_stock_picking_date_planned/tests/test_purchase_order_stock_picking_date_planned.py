###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import TransactionCase


class TestPurchaseOrderStockPickingDatePlanned(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 50,
            'list_price': 50,
        })
        self.purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': self.purchase.id,
            'product_id': self.product.id,
            'price_unit': 100,
            'quantity': 1,
        })
        line.onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line._cache))

    def test_set_custom_date_planned(self):
        now = fields.Datetime.now()
        self.purchase.custom_date_planned = now + relativedelta(days=5)
        self.purchase.button_confirm()
        picking = self.purchase.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(self.purchase.picking_ids), 1)
        self.assertEquals(len(self.purchase.picking_ids.move_lines), 1)
        self.assertEquals(picking.scheduled_date, now + relativedelta(days=5))
        self.assertEquals(
            picking.move_lines[0].date_expected, now + relativedelta(days=5))

    def test_standard_date(self):
        self.purchase.custom_date_planned = False
        self.purchase.button_confirm()
        picking = self.purchase.picking_ids[0]
        picking.action_confirm()
        self.assertEquals(len(self.purchase.picking_ids), 1)
        self.assertEquals(len(self.purchase.picking_ids.move_lines), 1)
        self.assertFalse(self.purchase.custom_date_planned)
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertTrue(picking.scheduled_date)
        self.assertTrue(picking.move_lines[0].date_expected)
