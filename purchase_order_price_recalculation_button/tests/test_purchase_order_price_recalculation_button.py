###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestPurchaseOrderPriceRecalculationButton(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Test product',
            'default_code': 'TEST-01',
            'standard_price': 10,
            'list_price': 20,
        })
        self.purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'date_planned': fields.Date.today(),
                    'product_qty': 1,
                    'product_uom': self.product.uom_id.id,
                    'price_unit': self.product.standard_price,
                })
            ],
        })

    def test_purchase_price_recalculation_button(self):
        self.assertEqual(
            self.purchase.order_line[0].price_unit, self.product.standard_price)
        old_standard_price = self.product.standard_price
        old_amount_total = self.purchase.amount_total
        self.purchase.button_recalculate_purchase_prices()
        self.assertNotEqual(
            self.purchase.order_line[0].price_unit, old_standard_price)
        self.assertNotEqual(self.purchase.amount_total, old_amount_total)
