###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestProjectCurrentBalance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.start_date = fields.Date.today().replace(day=1)
        self.employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not self.employee:
            self.employee = self.env['hr.employee'].create({
                'name': 'Balance Employee',
                'user_id': self.env.user.id,
                'company_id': self.env.company.id,
            })
        self.project = self.env['project.project'].create({
            'name': 'Balance Project',
            'extra_balance': 10.0,
            'extra_balance_date': self.start_date,
        })

    def _create_timesheet(self, date, unit_amount):
        return self.env['account.analytic.line'].create({
            'name': 'Timesheet',
            'project_id': self.project.id,
            'date': date,
            'unit_amount': unit_amount,
            'employee_id': self.employee.id,
        })

    def test_current_balance_without_timesheets(self):
        self.assertEqual(self.project.current_balance, 10.0)

    def test_current_balance_subtracts_timesheets(self):
        self._create_timesheet(self.start_date + timedelta(days=4), 3.5)
        self.assertEqual(self.project.current_balance, 6.5)

    def test_current_balance_respects_extra_balance_date(self):
        self._create_timesheet(self.start_date - timedelta(days=1), 4.0)
        self._create_timesheet(self.start_date + timedelta(days=4), 2.0)
        self.assertEqual(self.project.current_balance, 8.0)
