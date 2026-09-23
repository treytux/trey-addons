###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import common


class TestAccountPaymentTermAvoidWeekend(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 30,
        })
        self.payment_days = 30
        self.payment_term = self.env['account.payment.term'].create({
            'name': '30 days test',
            'line_ids': [
                (0, 0, {
                    'value': 'balance',
                    'value_amount': 0.0,
                    'sequence': 500,
                    'days': self.payment_days,
                    'option': 'day_after_invoice_date',
                }),
            ],
        })

    def get_days_difference(self, date):
        if date.weekday() == 0:
            return -1
        elif date.weekday() == 1:
            return -2
        elif date.weekday() == 2:
            return 4
        elif date.weekday() == 3:
            return 3
        elif date.weekday() == 4:
            return 2
        elif date.weekday() == 5:
            return 1
        elif date.weekday() == 6:
            return 0

    def set_payment_date_in_weekend_range(self):
        date = fields.Date.today() + relativedelta(days=self.payment_days)
        if date.weekday() in [5, 6]:
            return True
        elif date.weekday() == 0:
            self.payment_term.line_ids[0].days = self.payment_days - 1
        elif date.weekday() == 1:
            self.payment_term.line_ids[0].days = self.payment_days - 2
        elif date.weekday() == 2:
            self.payment_term.line_ids[0].days = self.payment_days + 4
        elif date.weekday() == 3:
            self.payment_term.line_ids[0].days = self.payment_days + 3
        elif date.weekday() == 4:
            self.payment_term.line_ids[0].days = self.payment_days + 2

    def test_account_payment_term_weekend_01(self):
        self.set_payment_date_in_weekend_range()
        self.assertFalse(self.payment_term.avoid_payment_weekend)
        self.payment_term.avoid_payment_weekend = True
        self.assertTrue(self.payment_term.avoid_payment_weekend)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'payment_term_id': self.payment_term.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.payment_term_id)
        self.assertEqual(sale.payment_term_id, self.payment_term)
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        self.assertTrue(invoice.date_due.weekday() not in [5, 6])

    def test_account_payment_term_weekend_02(self):
        self.set_payment_date_in_weekend_range()
        self.assertFalse(self.payment_term.avoid_payment_weekend)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'payment_term_id': self.payment_term.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.payment_term_id)
        self.assertEqual(sale.payment_term_id, self.payment_term)
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        self.assertTrue(invoice.date_due.weekday() in [5, 6])

    def test_account_payment_term_weekend_holiday_03(self):
        module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'account_payment_term_extension'),
            ('state', '=', 'installed'),
        ])
        if not module:
            self.skipTest('No module account_payment_term_extension installed')
        self.set_payment_date_in_weekend_range()
        self.assertFalse(self.payment_term.avoid_payment_weekend)
        self.payment_term.avoid_payment_weekend = True
        self.assertTrue(self.payment_term.avoid_payment_weekend)
        self.assertEqual(len(self.payment_term.holiday_ids), 0)
        date = fields.Date.today() + relativedelta(days=self.payment_days)
        days_delay = self.get_days_difference(date)
        holiday_date = date + relativedelta(days=days_delay + 1)
        date_postponed = holiday_date + relativedelta(days=1)
        self.payment_term.write({
            'holiday_ids': [
                (0, 0, {
                    'holiday': holiday_date,
                    'date_postponed': date_postponed,
                })
            ]
        })
        self.assertEqual(len(self.payment_term.holiday_ids), 1)
        holiday_id = self.payment_term.holiday_ids[0]
        self.assertEqual(holiday_id.holiday, holiday_date)
        self.assertEqual(holiday_id.date_postponed, date_postponed)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'payment_term_id': self.payment_term.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.payment_term_id)
        self.assertEqual(sale.payment_term_id, self.payment_term)
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertTrue(invoice.date_invoice)
        self.assertTrue(invoice.date_due)
        self.assertTrue(invoice.date_due.weekday() not in [5, 6])
        self.assertNotEqual(invoice.date_due, holiday_date)
        self.assertEqual(invoice.date_due, date_postponed)
