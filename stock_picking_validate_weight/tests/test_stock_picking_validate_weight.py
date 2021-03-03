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

    def test_wizard(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 20,
            })],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(picking.weight, 200)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(len(picking.move_lines), 1)
        wizard = self.env['stock.immediate.transfer'].create(
            {'pick_ids': [(4, picking.id)]})
        self.assertEquals(wizard.weight, 200)
        wizard.weight = 10
        wizard.process()
        self.assertEquals(picking.shipping_weight, 10)
