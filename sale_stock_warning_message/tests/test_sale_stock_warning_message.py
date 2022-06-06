###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAgreementAcceptance(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 100,
        })
        self.location = self.env.ref('stock.stock_location_stock')

    def test_check_not_warning_message(self):
        quantity = 10.0
        quant_obj = self.env['stock.quant']
        quant_obj._update_available_quantity(
            self.product, self.location, quantity)
        self.assertEqual(self.product.qty_available, quantity)
        product_uom_qty = 20
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': product_uom_qty,
                'price_unit': self.product.list_price,
            })],
        })
        message = sale.order_line[0]._onchange_product_id_check_availability()
        self.assertEqual(message, {})
        sale.action_confirm()
