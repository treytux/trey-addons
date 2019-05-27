###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestPartnerBlockingSale(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_blocked = self.env.ref(
            'partner_blocking_sale.partner_blocked')
        self.partner_allowed = self.env.ref(
            'partner_blocking_sale.partner_allowed')

    def test_sale_with_partner_allowed(self):
        product = self.env.ref('product.product_product_4')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_allowed.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 10})]
        })
        sale.onchange_partner_id()
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')

    def test_sale_with_partner_blocked(self):
        product = self.env.ref('product.product_product_4')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_blocked.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 10})]
        })
        self.assertRaises(UserError, sale.onchange_partner_id)
