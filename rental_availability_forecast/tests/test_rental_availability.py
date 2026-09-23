##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestRentalAvailability(TransactionCase):

    def setUp(self):
        super().setUp()
        self.service_product = self.env.ref(
            'sale_rental.rent_product_product_25')
        self.product = self.service_product.rented_product_id
        self.warehouse = self.env.ref('stock.warehouse0')
        self.partner = self.env['res.partner'].create({
            'name': 'Rental availability test',
        })
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.product.id,
            'inventory_quantity': 10,
            'location_id': self.warehouse.rental_in_location_id.id,
        }).action_apply_inventory()

    def _order(self, start, end, quantity=1, state='sale'):
        days = (end - start).days + 1
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id, 'warehouse_id': self.warehouse.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id, 'product_id': self.service_product.id,
            'start_date': start, 'end_date': end, 'rental_qty': quantity,
            'rental': True, 'rental_type': 'new_rental',
            'product_uom_qty': days * quantity, 'number_of_days': days,
        })
        if state == 'sale':
            order.action_confirm()
        return order

    def _availability(self, start, end, quantity=1, **kwargs):
        return self.env['rental.availability']._get_rental_availability(
            self.product, self.warehouse, start, end, quantity, **kwargs)

    def test_enough_current_stock(self):
        result = self._availability(
            fields.Date.today(), fields.Date.today(), 3)
        self.assertTrue(result['is_available'])
        self.assertEqual(result['available_quantity'], 10)

    def test_availability_after_return(self):
        today = fields.Date.today()
        self._order(today + timedelta(days=1), today + timedelta(days=3), 8)
        result = self._availability(
            today + timedelta(days=4), today + timedelta(days=5), 8)
        self.assertTrue(result['is_available'])

    def test_late_return_remains_unavailable(self):
        today = fields.Date.today()
        self._order(today + timedelta(days=1), today + timedelta(days=5), 8)
        result = self._availability(
            today + timedelta(days=3), today + timedelta(days=6), 8)
        self.assertFalse(result['is_available'])

    def test_inclusive_end_date_conflicts(self):
        today = fields.Date.today()
        self._order(today + timedelta(days=1), today + timedelta(days=3), 6)
        result = self._availability(
            today + timedelta(days=3), today + timedelta(days=3), 6)
        self.assertFalse(result['is_available'])
        self.assertEqual(
            result['first_insufficient_date'], today + timedelta(days=3))

    def test_return_starts_day_after_end(self):
        today = fields.Date.today()
        self._order(today + timedelta(days=1), today + timedelta(days=3), 10)
        self.assertFalse(self._availability(
            today + timedelta(days=3),
            today + timedelta(days=3), 1)['is_available'])
        self.assertTrue(self._availability(
            today + timedelta(days=4),
            today + timedelta(days=4), 10)['is_available'])

    def test_overlapping_rentals_use_minimum_projection(self):
        today = fields.Date.today()
        first = self._order(
            today + timedelta(days=1), today + timedelta(days=4), 6)
        self._order(today + timedelta(days=2), today + timedelta(days=3), 5)
        result = self._availability(
            today + timedelta(days=1), today + timedelta(days=4), 1)
        self.assertEqual(
            result['first_insufficient_date'], today + timedelta(days=2))
        self.assertTrue(first)

    def test_draft_and_sent_do_not_block_hard_availability(self):
        today = fields.Date.today()
        for state in ('draft', 'sent'):
            order = self._order(
                today + timedelta(days=1),
                today + timedelta(days=2), 10, state=False)
            if state == 'sent':
                order.action_quotation_sent()
        self.assertTrue(
            self._availability(
                today + timedelta(days=1),
                today + timedelta(days=2), 10)['is_available'])

    def test_draft_and_sent_are_potential_demand(self):
        today = fields.Date.today()
        order = self._order(today, today + timedelta(days=1), 2, state=False)
        order.action_quotation_sent()
        lines = self.env['rental.forecast'].generate(
            self.product, self.warehouse, today, days=2)
        self.assertEqual(
            lines.filtered(lambda ln: ln.date == today).potential_demand, 2)

    def test_confirmation_does_not_show_forecast_warning(self):
        today = fields.Date.today()
        order = self._order(today, today, 20, state=False)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_forecast_contains_availability_intervals(self):
        today = fields.Date.today()
        lines = self.env['rental.forecast'].generate(
            self.product, self.warehouse, today, days=12 * 30)
        self.assertLess(len(lines), 12 * 30)
        self.assertTrue(all(line.date_end >= line.date for line in lines))
        self.assertTrue(all(
            line.company_id == self.warehouse.company_id for line in lines))

    def test_generate_for_selected_warehouse(self):
        forecast = self.env['rental.forecast']
        line_ids = forecast.generate_for_product_warehouse(
            self.product.id, self.warehouse.id)
        lines = forecast.browse(line_ids)
        self.assertTrue(lines)
        self.assertEqual(lines.warehouse_id, self.warehouse)
        self.assertEqual(lines.company_id, self.warehouse.company_id)
