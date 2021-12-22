###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductListPriceFromMargin(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 100,
            'list_price': 125,
        })
        self.product2 = self.env['product.product'].create({
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 500,
            'list_price': 720,
        })
        self.product3 = self.env['product.product'].create({
            'company_id': False,
            'name': 'Test product 3',
            'list_price': 0,
        })
        self.pricelist_test = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [
                (0, 0, {
                    'applied_on': '1_product',
                    'product_tmpl_id': self.product2.product_tmpl_id.id,
                    'compute_price': 'percentage',
                    'percent_price': 50,
                }),
                (0, 0, {
                    'applied_on': '1_product',
                    'product_tmpl_id': self.product3.product_tmpl_id.id,
                    'compute_price': 'percentage',
                    'percent_price': 40,
                }),
            ],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'property_product_pricelist': self.pricelist_test.id,
        })

    def test_simulator_wizard(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 125,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
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

    def test_sale_order_line_pl_discount(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product2.id,
                    'product_uom_qty': 1}),
            ]
        })
        sale.order_line[0].product_id_change()
        self.assertEquals(sale.order_line[0].product_id.lst_price, 720)
        self.assertEquals(sale.order_line[0].pl_discount, 50)
        self.assertEquals(sale.order_line[0].price_unit, 360)
        sale.order_line[0].product_id = self.product3.id
        sale.order_line[0].product_id_change()
        self.assertEquals(sale.order_line[0].product_id.lst_price, 0)
        self.assertEquals(sale.order_line[0].pl_discount, 0)
        self.assertEquals(sale.order_line[0].price_unit, 0)
        sale.order_line[0].product_id = self.product.id
        sale.order_line[0].product_id_change()
        self.assertEquals(sale.order_line[0].product_id.lst_price, 125)
        self.assertEquals(sale.order_line[0].pl_discount, 0)
        self.assertEquals(sale.order_line[0].price_unit, 125)
