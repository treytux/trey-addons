###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import unittest

from odoo import Command
from odoo.addons.payment.tests.common import PaymentCommon


class TestPaymentTransaction(PaymentCommon):

    def setUp(self):
        super().setUp()
        if 'product.product' not in self.env:
            raise unittest.SkipTest('requires product')
        self.provider = self._prepare_provider(
            code='custom',
            update_values={'confirm_orders_automatically': True})
        self.product = self.env['product.product'].create({
            'name': 'test product',
            'list_price': self.amount,
        })

    def _create_sale_order_transaction(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        tx = self._create_transaction(
            flow='direct', sale_order_ids=[sale_order.id])
        return sale_order, tx

    def test_custom_transaction_confirms_sale_order(self):
        sale_order, tx = self._create_sale_order_transaction()
        tx._process_notification_data({})
        self.assertEqual(tx.state, 'pending')
        self.assertEqual(sale_order.state, 'sale')

    def test_custom_transaction_does_not_confirm_without_setting(self):
        self.provider.confirm_orders_automatically = False
        sale_order, tx = self._create_sale_order_transaction()
        tx._process_notification_data({})
        self.assertEqual(tx.state, 'pending')
        self.assertEqual(sale_order.state, 'sent')
