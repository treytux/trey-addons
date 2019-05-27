###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestDeliveryNotAutoAddShippingCost(TransactionCase):

    def setUp(self):
        super().setUp()
        self.carrier = self.env.ref('delivery.normal_delivery_carrier')
        self.product = self.env.ref(
            'product.product_product_7_product_template').product_variant_id
        self.partner = self.env.ref('base.res_partner_3')
        self.inventory(self.product, 100)

    def inventory(self, product, qty):
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'add %s products for tests' % qty,
            'filter': 'product',
            'location_id': location.id,
            'product_id': product.id,
            'exhausted': True})
        inventory.action_start()
        stock_loc = self.env.ref('stock.stock_location_stock')
        inventory.line_ids.write({
            'product_qty': qty,
            'location_id': stock_loc.id})
        inventory.action_done()

    def test_delivery_cost_not_auto_add(self):
        self.carrier.auto_shipping_cost = False
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        sale.get_delivery_price()
        sale.action_confirm()
        self.assertTrue(
            all([not line.is_delivery for line in sale.order_line]))
        sale.picking_ids[0].action_confirm()
        sale.picking_ids[0].action_assign()
        sale.picking_ids[0].action_done()
        self.assertTrue(
            all([not line.is_delivery for line in sale.order_line]))

    def test_delivery_cost_allowed_auto_add(self):
        self.carrier.auto_shipping_cost = True
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        sale.get_delivery_price()
        sale.action_confirm()
        self.assertTrue(
            all([not line.is_delivery for line in sale.order_line]))
        sale.picking_ids[0].action_confirm()
        sale.picking_ids[0].action_assign()
        sale.picking_ids[0].action_done()
        self.assertFalse(
            all([not line.is_delivery for line in sale.order_line]))
