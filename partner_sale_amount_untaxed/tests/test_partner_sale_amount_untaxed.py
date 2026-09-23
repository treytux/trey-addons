###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestResPartnerSaleAmountUntaxed(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_obj = self.env['res.partner']
        self.sale_order_obj = self.env['sale.order']
        self.sale_order_line_obj = self.env['sale.order.line']

    def test_sale_amount_untaxed(self):
        """Test that the sale_amount_untaxed field is computed correctly."""
        partner = self.partner_obj.create({'name': 'Test Partner'})
        sale_order = self.sale_order_obj.create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': self.env.ref('product.product_product_25').id,
                'product_uom_qty': 2,
                'price_unit': 100,
            })]
        })
        self.assertEqual(sale_order.amount_untaxed, 200)
