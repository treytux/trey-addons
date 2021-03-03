###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderLineMoveToOptional(TransactionCase):

    def test_simulator_wizard(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        product2 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 125,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product2.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        self.assertEquals(len(sale.order_line), 2)
        self.assertEquals(len(sale.sale_order_option_ids), 0)
        sale.order_line[0].move_to_optional()
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(len(sale.sale_order_option_ids), 1)
