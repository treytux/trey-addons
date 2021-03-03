###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import common


class TestSaleReturnHistorical(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.sale_historical = self.env['sale.order.historical'].create({
            'name': 'Order Test',
        })
        sale_order_historical_line = self.env['sale.order.historical.line']
        self.historical_line_1 = sale_order_historical_line.create({
            'name': 'Order Line Test 1',
            'order_id': self.sale_historical.id,
        })

    def test_sale_return_historical(self):
        self.assertTrue(self.sale_historical.available_return)
        self.assertEqual(len(self.sale_historical.order_line_ids), 1)
        day = (datetime.now() + timedelta(days=1)).date()
        self.historical_line_1.available_return_date = day
        self.assertTrue(self.historical_line_1.available_return)
        self.assertTrue(self.sale_historical.available_return)
        day = (datetime.now() - timedelta(days=1)).date()
        self.historical_line_1.available_return_date = day
        self.assertFalse(self.historical_line_1.available_return)
        self.assertFalse(self.sale_historical.available_return)
        self.historical_line_1.available_return_date = fields.Date.today()
        self.assertTrue(self.historical_line_1.available_return)
        self.assertTrue(self.sale_historical.available_return)

    def test_several_sale_return_historical_lines(self):
        self.assertTrue(self.sale_historical.available_return)
        sale_order_historical_line = self.env['sale.order.historical.line']
        self.historical_line_2 = sale_order_historical_line.create({
            'name': 'Order Line Test 2',
            'order_id': self.sale_historical.id,
        })
        self.assertEqual(len(self.sale_historical.order_line_ids), 2)
        day_1 = (datetime.now() + timedelta(days=1)).date()
        day_2 = (datetime.now() - timedelta(days=1)).date()
        self.historical_line_1.available_return_date = day_1
        self.historical_line_2.available_return_date = day_1
        self.assertTrue(self.historical_line_1.available_return)
        self.assertTrue(self.historical_line_2.available_return)
        self.assertTrue(self.sale_historical.available_return)
        self.historical_line_1.available_return_date = day_2
        self.assertFalse(self.historical_line_1.available_return)
        self.assertTrue(self.historical_line_2.available_return)
        self.assertTrue(self.sale_historical.available_return)
        self.historical_line_1.available_return_date = day_1
        self.historical_line_2.available_return_date = day_2
        self.assertTrue(self.historical_line_1.available_return)
        self.assertFalse(self.historical_line_2.available_return)
        self.assertTrue(self.sale_historical.available_return)
        self.historical_line_1.available_return_date = day_2
        self.assertFalse(self.historical_line_1.available_return)
        self.assertFalse(self.historical_line_2.available_return)
        self.assertFalse(self.sale_historical.available_return)
