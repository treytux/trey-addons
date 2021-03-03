###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPickingValidateCarrier(TransactionCase):

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

    def test_wizard(self):
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        carrier = self.env['delivery.carrier'].create({
            'name': 'Test carrier',
            'delivery_type': 'fixed',
            'product_id': product_shipping_cost.id,
            'fixed_price': 99.99,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': carrier.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 20,
            })],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(picking.carrier_id, carrier)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(len(picking.move_lines), 1)
        wizard = self.env['stock.immediate.transfer'].create(
            {'pick_ids': [(4, picking.id)]})
        self.assertEquals(wizard.carrier_id, carrier)
        picking.carrier_id = False
        self.assertFalse(picking.carrier_id.exists())
        wizard.process()
        self.assertEquals(picking.carrier_id, carrier)
