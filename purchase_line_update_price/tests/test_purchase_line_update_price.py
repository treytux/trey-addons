###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.tests.common as common
from odoo.exceptions import UserError, ValidationError


class TestPurchaseLineUpdatePrice(common.TransactionCase):

    def setUp(self):
        super(TestPurchaseLineUpdatePrice, self).setUp()
        self.supplier1 = self.env['res.partner'].create({
            'name': 'Test supplier 1',
            'supplier': True,
        })
        self.tax_21 = self.env['account.tax'].create({
            'name': '21%',
            'amount_type': 'percent',
            'amount': 21,
            'type_tax_use': 'purchase',
        })
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.product1 = self.env['product.product'].create({
            'name': 'Test product 1',
            'type': 'product',
            'standard_price': 1,
            'list_price': 1,
            'supplier_taxes_id': [(6, 0, [self.tax_21.id])],
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier1.id,
                'delay': 1,
                'price': 100,
            })],
        })
        self.product2 = self.env['product.product'].create({
            'name': 'Test product 2',
            'type': 'product',
            'standard_price': 1,
            'list_price': 2,
            'supplier_taxes_id': [(6, 0, [self.tax_21.id])],
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier1.id,
                'delay': 1,
                'price': 200,
            })],
        })
        data_lines_p1 = {
            'product_id': self.product1.id,
            'price_unit': self.product1.standard_price,
            'quantity': 2,
        }
        self.purchase1 = self.create_purchase_order(
            self.supplier1, [data_lines_p1])
        data_line_p2_1 = {
            'product_id': self.product1.id,
            'price_unit': self.product1.standard_price,
            'quantity': 2,
        }
        data_line_p2_2 = {
            'product_id': self.product2.id,
            'price_unit': self.product2.standard_price,
            'quantity': 3,
        }
        self.purchase2 = self.create_purchase_order(
            self.supplier1, [data_line_p2_1, data_line_p2_2])

    def create_purchase_order(self, partner, data_lines):
        purchase = self.env['purchase.order'].create({
            'partner_id': partner.id,
        })
        line_obj = self.env['purchase.order.line']
        for data_line in data_lines:
            data_line.update({
                'order_id': purchase.id,
            })
            line = line_obj.new(data_line)
            line.onchange_product_id()
            line_obj.create(line_obj._convert_to_write(line._cache))
        return purchase

    def create_wizard(
            self, purchases, dollar_factor, carrier_factor, extra_factor):
        wizard = self.env['purchase.line.update.price'].with_context({
            'active_model': 'purchase.order',
            'active_ids': purchases.ids,
            'active_id': purchases[0].id,
        })
        return wizard.create({
            'dollar_factor': dollar_factor,
            'carrier_factor': carrier_factor,
            'extra_factor': extra_factor,
        })

    def calculate_new_price(self, price_unit, wizard):
        return (
            price_unit / wizard.dollar_factor
            * wizard.carrier_factor * wizard.extra_factor
        )

    def test_update_price_one_line(self):
        self.assertEquals(self.purchase1.order_line.price_unit, 100)
        self.assertEquals(self.purchase1.amount_total, 121)
        wizard = self.create_wizard(self.purchase1, 0.85, 0.5, 0.25)
        wizard.update_prices()
        self.calculate_new_price(self.purchase1.order_line.price_unit, wizard)
        self.assertEquals(
            self.purchase1.order_line.price_unit, round(14.71, 2))
        self.assertEquals(self.purchase1.amount_total, round(14.71 * 1.21, 2))

    def test_update_price_several_lines(self):
        line_product1 = self.purchase2.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(line_product1.price_unit, 100)
        line_product2 = self.purchase2.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(line_product2.price_unit, 200)
        self.assertEquals(self.purchase2.amount_total, 363)
        wizard = self.create_wizard(self.purchase2, 0.85, 0.5, 0.25)
        wizard.update_prices()
        self.calculate_new_price(line_product1.price_unit, wizard)
        self.assertEquals(
            line_product1.price_unit, round(14.71, 2))
        self.calculate_new_price(line_product2.price_unit, wizard)
        self.assertEquals(
            line_product2.price_unit, round(29.41, 2))
        self.assertEquals(
            self.purchase2.amount_total, round((14.71 + 29.41) * 1.21, 2))

    def test_update_price_no_draft(self):
        self.purchase1.button_confirm()
        self.assertEquals(self.purchase1.state, 'purchase')
        wizard = self.create_wizard(self.purchase1, 0.85, 0.5, 0.25)
        with self.assertRaises(UserError):
            wizard.update_prices()

    def test_update_price_wizard_from_several_purchases(self):
        self.assertEquals(self.purchase1.order_line.price_unit, 100)
        self.assertEquals(self.purchase1.amount_total, 121)
        line_product1 = self.purchase2.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(line_product1.price_unit, 100)
        line_product2 = self.purchase2.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(line_product2.price_unit, 200)
        self.assertEquals(self.purchase2.amount_total, 363)
        purchases = self.purchase1
        purchases |= self.purchase2
        wizard = self.create_wizard(purchases, 0.85, 0.5, 0.25)
        wizard.update_prices()
        self.assertEquals(
            self.purchase1.order_line.price_unit, round(14.71, 2))
        self.assertEquals(self.purchase1.amount_total, round(14.71 * 1.21, 2))
        self.assertEquals(line_product1.price_unit, round(14.71, 2))
        self.assertEquals(line_product2.price_unit, round(29.41, 2))
        self.assertEquals(
            self.purchase2.amount_total, round((14.71 + 29.41) * 1.21, 2))

    def test_update_factor_greater_than_zero(self):
        self.assertEquals(self.purchase1.order_line.price_unit, 100)
        self.assertEquals(self.purchase1.amount_total, 121)
        with self.assertRaises(ValidationError):
            self.create_wizard(self.purchase1, 0, -0.5, 0.25)
