###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductMinQuantity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_1')
        self.product = self.env.ref('product.product_order_01')

    def create_order(self, qty):
        order_line = {
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': qty,
            'product_uom': self.product.uom_id.id,
            'price_unit': self.product.list_price,
        }
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, order_line)],
            'pricelist_id': self.env.ref('product.list0').id,
        })

    def test_min_quantity(self):
        self.product.min_order_qty = 10
        self.assertRaises(UserError, self.create_order, 1)
        self.assertRaises(UserError, self.create_order, 9)
        sale = self.create_order(11)
        self.assertEqual(len(sale.order_line), 1)

    def test_min_quantity_more_tath_one_line(self):
        self.product.min_order_qty = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Line without product'}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 10}),
            ]
        })
        with self.assertRaises(UserError):
            sale.order_line.write({'product_uom_qty': 0})
