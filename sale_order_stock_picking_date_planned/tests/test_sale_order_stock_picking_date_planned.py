###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleOrderStockPickingDatePlanned(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 50,
            'list_price': 50,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'commitment_date': fields.Datetime.now(),
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })

    def test_set_date_planned(self):
        now = fields.Datetime.now()
        self.sale.date_planned = now + relativedelta(days=5)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        self.assertEquals(len(self.sale.picking_ids.move_lines), 1)
        self.assertEquals(picking.scheduled_date, now + relativedelta(days=5))
        self.assertEquals(
            picking.move_lines[0].date_expected, now + relativedelta(days=5))

    def test_standard_date(self):
        self.sale.date_planned = False
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        self.assertEquals(len(self.sale.picking_ids.move_lines), 1)
        company = self.env.ref('base.main_company')
        out_date = (fields.Datetime.from_string(self.sale.date_order)
                    + timedelta(days=self.product.sale_delay)
                    - timedelta(days=company.security_lead))
        min_date = fields.Datetime.from_string(picking.scheduled_date)
        self.assertTrue(abs(min_date - out_date) <= timedelta(seconds=1))
        security_delay = timedelta(days=self.sale.company_id.security_lead)
        commitment_date = fields.Datetime.from_string(
            self.sale.commitment_date)
        right_date = commitment_date - security_delay
        for line in self.sale.order_line:
            self.assertEqual(line.move_ids[0].date_expected, right_date)
