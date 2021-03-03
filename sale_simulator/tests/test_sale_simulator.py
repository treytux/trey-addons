###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductListPriceFromMargin(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 100,
            'list_price': 125,
        })
        self.product2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 500,
            'list_price': 725,
        })

    def test_simulator_wizard(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 125,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        action = sale.action_open_simulator()
        wizard = self.env['sale.open.simulator'].browse(action['res_id'])
        self.assertEquals(len(wizard.line_ids), 2)
        line = wizard.line_ids[0]
        self.assertEquals(line.price_unit, 125)
        self.assertEquals(sale.order_line[0].standard_price, 0)
        wizard.action_update()
        self.assertEquals(sale.order_line[0].standard_price, 100)
        sale.order_line[0].product_id = self.product2.id
        sale.order_line[0].product_id_change()
        self.assertEquals(sale.order_line[0].standard_price, 500)
        action = sale.action_open_simulator()
        wizard = self.env['sale.open.simulator'].browse(action['res_id'])
        self.assertEquals(len(wizard.line_ids), 2)
        line = wizard.line_ids[0]
        self.assertEquals(line.standard_price, 500)
