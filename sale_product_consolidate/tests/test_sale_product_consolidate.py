###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests import common


class TestSaleProductConsolidate(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'service',
        })

    def _create_order(self, product=None):
        product = product or self.product
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
            })],
        })

    def test_confirm_order_with_non_consolidated_product(self):
        order = self._create_order()
        with self.assertRaises(UserError) as error:
            order.action_confirm()
        self.assertEqual(
            str(error.exception),
            'You cannot confirm a sale order with non-consolidated products. '
            '\n-Test product')
        self.assertEqual(order.state, 'draft')

    def test_confirm_order_with_consolidated_product(self):
        self.product.is_consolidated = True
        order = self._create_order()
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_confirm_multiple_orders_with_invalid_product(self):
        consolidated_product = self.env['product.product'].create({
            'name': 'Consolidated product',
            'type': 'service',
            'is_consolidated': True,
        })
        valid_order = self._create_order(consolidated_product)
        invalid_order = self._create_order()
        with self.assertRaises(UserError) as error:
            (valid_order | invalid_order).action_confirm()
        self.assertEqual(
            str(error.exception),
            'You cannot confirm a sale order with non-consolidated products. '
            '\n-Test product')
        self.assertEqual(valid_order.state, 'draft')
        self.assertEqual(invalid_order.state, 'draft')
