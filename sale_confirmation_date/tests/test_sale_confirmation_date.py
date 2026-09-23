###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestSaleConfirmationDate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })

    def create_sale(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'date_order': datetime.now() - timedelta(minutes=5),
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10,
            })],
        })
        return sale

    def test_confirm_sale(self):
        sale_order = self.create_sale()
        self.assertTrue(sale_order.date_order)
        self.assertFalse(sale_order.confirmation_date)
        sale_order.action_confirm()
        self.assertTrue(sale_order.date_order)
        self.assertNotEqual(
            sale_order.confirmation_date, sale_order.date_order)
