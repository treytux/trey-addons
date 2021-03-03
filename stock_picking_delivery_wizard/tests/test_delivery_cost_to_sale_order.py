###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestDeliveryCostToSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_18 = self.env.ref('base.res_partner_18')
        self.product_4 = self.env.ref('product.product_product_4')
        self.product_uom_kgm = self.env.ref('uom.product_uom_kgm')
        self.normal_delivery = self.env.ref('delivery.normal_delivery_carrier')
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'order_line': [(0, 0, {
                'name': 'POP Doctor Simon',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_4.uom_id.id,
                'price_unit': 750.00,
            })],
        })

    def test_not_delivery_cost(self):
        self.assertFalse(self.sale_order.delivery_cost_to_sale_order)
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids)
        picking = self.sale_order.picking_ids
        picking.carrier_id = self.normal_delivery.id,
        picking.move_lines.write({
            'quantity_done': 1,
        })
        self.assertIsNone(picking.button_validate())
        self.assertTrue(picking.action_done())
        delivery_lines = self.sale_order.mapped('order_line').filtered(
            lambda l: l.is_delivery)
        self.assertFalse(delivery_lines)

    def test_delivery_cost(self):
        self.sale_order.delivery_cost_to_sale_order = True
        self.assertTrue(self.sale_order.delivery_cost_to_sale_order)
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids)
        picking = self.sale_order.picking_ids
        picking.carrier_id = self.normal_delivery.id,
        picking.move_lines.write({
            'quantity_done': 1,
        })
        self.assertIsNone(picking.button_validate())
        self.assertTrue(picking.action_done())
        delivery_lines = self.sale_order.mapped('order_line').filtered(
            lambda l: l.is_delivery is True)
        self.assertTrue(delivery_lines)
