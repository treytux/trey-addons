###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleSimulatorCumulativeDiscount(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product01 = self.env['product.product'].create({
            'company_id': False,
            'name': 'Test product 1',
            'list_price': 125,
        })
        self.product02 = self.env['product.product'].create({
            'company_id': False,
            'name': 'Test product 2',
            'list_price': 720,
        })
        self.pricelist_test = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [
                (0, 0, {
                    'applied_on': '1_product',
                    'product_tmpl_id': self.product02.product_tmpl_id.id,
                    'compute_price': 'percentage',
                    'percent_price': 50,
                }),
            ],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'property_product_pricelist': self.pricelist_test.id,
        })

    def test_01_onchange(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product01.id,
                    'price_unit': 125,
                    'product_uom_qty': 1,
                    'multiple_discount': 10,
                }),
                (0, 0, {
                    'product_id': self.product02.id,
                    'price_unit': 360,
                    'product_uom_qty': 2,
                    'multiple_discount': 20,
                }),
            ]
        })
        action = sale.action_open_simulator()
        wizard = self.env['sale.open.simulator'].browse(action['res_id'])
        line = wizard.line_ids[0]
        self.assertEqual(
            line.multiple_discount, sale.order_line[0].multiple_discount)
        self.assertEqual(line.price_subtotal, 112.5)
        wizard.write({
            'multiple_discount': '15+5',
        })
        self.assertEqual(wizard.multiple_discount, '15+5')
        wizard.onchange_multiple_discount()
        self.assertEqual(line.multiple_discount, '15+5')
        self.assertEqual(line.price_subtotal, 100.94)
        line = wizard.line_ids[1]
        self.assertEqual(line.multiple_discount, '15+5')
        self.assertEqual(line.price_subtotal, 581.4)
