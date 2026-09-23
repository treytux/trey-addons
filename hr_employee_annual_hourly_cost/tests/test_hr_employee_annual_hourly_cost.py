###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHrEmployeeAnnualHourlyCost(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not self.employee:
            self.employee = self.env['hr.employee'].create({
                'name': 'Annual Cost Employee',
                'user_id': self.env.user.id,
                'company_id': self.env.company.id,
                'hourly_cost': 42.0,
            })
        self.employee.hourly_cost = 42.0

    def test_get_period_hourly_cost_uses_period_value(self):
        self.env['hr.employee.annual.hourly.cost'].create({
            'employee_id': self.employee.id,
            'date_start': '2023-01-01',
            'date_end': '2023-12-31',
            'hourly_cost': 30.0,
        })
        self.assertEqual(
            self.employee.get_period_hourly_cost('2023-06-01'), 30.0)

    def test_get_period_hourly_cost_fallbacks_to_current(self):
        self.assertEqual(
            self.employee.get_period_hourly_cost('2024-06-01'), 42.0)

    def test_get_period_hourly_cost_uses_next_available_period(self):
        self.env['hr.employee.annual.hourly.cost'].create({
            'employee_id': self.employee.id,
            'date_start': '2023-01-01',
            'date_end': '2023-12-31',
            'hourly_cost': 30.0,
        })
        self.env['hr.employee.annual.hourly.cost'].create({
            'employee_id': self.employee.id,
            'date_start': '2025-01-01',
            'date_end': '2025-12-31',
            'hourly_cost': 55.0,
        })
        self.assertEqual(
            self.employee.get_period_hourly_cost('2022-06-01'), 30.0)
        self.assertEqual(
            self.employee.get_period_hourly_cost('2024-06-01'), 55.0)

    def test_get_period_hourly_cost_fallbacks_when_no_future_period(self):
        self.env['hr.employee.annual.hourly.cost'].create({
            'employee_id': self.employee.id,
            'date_start': '2021-01-01',
            'date_end': '2021-12-31',
            'hourly_cost': 25.0,
        })
        self.assertEqual(
            self.employee.get_period_hourly_cost('2022-06-01'), 42.0)

    def test_hourly_cost_periods_cannot_overlap(self):
        self.env['hr.employee.annual.hourly.cost'].create({
            'employee_id': self.employee.id,
            'date_start': '2024-01-01',
            'date_end': '2024-12-31',
            'hourly_cost': 30.0,
        })
        with self.assertRaises(ValidationError) as result:
            self.env['hr.employee.annual.hourly.cost'].create({
                'employee_id': self.employee.id,
                'date_start': '2024-06-01',
                'date_end': '2025-05-31',
                'hourly_cost': 35.0,
            })
        self.assertEqual(
            result.exception.args[0],
            'There is already an hourly cost period overlapping these dates '
            'for this employee.')

    def test_get_period_hourly_cost_uses_open_period_until_today(self):
        today = fields.Date.today()
        self.env['hr.employee.annual.hourly.cost'].create({
            'employee_id': self.employee.id,
            'date_start': '2024-01-01',
            'hourly_cost': 31.0,
        })
        self.assertEqual(
            self.employee.get_period_hourly_cost(today), 31.0)

    def test_open_period_start_date_cannot_be_future(self):
        today = fields.Date.today()
        future_date = fields.Date.add(today, days=1)
        with self.assertRaises(ValidationError) as result:
            self.env['hr.employee.annual.hourly.cost'].create({
                'employee_id': self.employee.id,
                'date_start': future_date,
                'hourly_cost': 33.0,
            })
        self.assertEqual(
            result.exception.args[0],
            'When end date is empty, start date must be lower than or '
            'equal to today.')

    def test_only_latest_period_can_have_empty_end_date(self):
        self.env['hr.employee.annual.hourly.cost'].create({
            'employee_id': self.employee.id,
            'date_start': '2025-01-01',
            'date_end': '2025-12-31',
            'hourly_cost': 30.0,
        })
        with self.assertRaises(ValidationError) as result:
            self.env['hr.employee.annual.hourly.cost'].create({
                'employee_id': self.employee.id,
                'date_start': '2024-01-01',
                'hourly_cost': 28.0,
            })
        self.assertEqual(
            result.exception.args[0],
            'Only the most recent period can have an empty end date.')
