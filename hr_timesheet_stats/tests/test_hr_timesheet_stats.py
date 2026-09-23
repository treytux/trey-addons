###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.tests import common


class TestHrTimesheetStats(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Company test',
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Employee',
        })
        self.account = self.env['account.analytic.account'].create({
            'name': 'Contract test analytic account',
        })
        self.project = self.env['project.project'].create({
            'name': 'Test project',
            'analytic_account_id': self.account.id,
        })
        self.task1 = self.env['project.task'].create({
            'name': 'Test task1',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'name': 'Old line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=3),
                    'unit_amount': 3,
                    'real_time': 3,
                    'employee_id': self.employee.id,
                }),
                (0, 0, {
                    'name': 'First line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 2,
                    'real_time': 3,
                    'employee_id': self.employee.id,
                }),
                (0, 0, {
                    'name': 'Second line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee.id,
                }),
                (0, 0, {
                    'name': 'Other line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee.id,
                }),
            ],
        })
        self.task2 = self.env['project.task'].create({
            'name': 'Test task2',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'name': 'Old line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=3),
                    'unit_amount': 3,
                    'real_time': 3,
                    'employee_id': self.employee.id,
                }),
                (0, 0, {
                    'name': 'First line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 2,
                    'real_time': 3,
                    'employee_id': self.employee.id,
                }),
                (0, 0, {
                    'name': 'Second line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee.id,
                }),
                (0, 0, {
                    'name': 'Other line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee.id,
                }),
            ],
        })

    def test_correct_quantity_hours(self):
        employee_real_hours = self.employee.total_real_hours()
        self.assertEqual(employee_real_hours, 22)
        employee_unit_amount = self.employee.total_unit_amount()
        self.assertEqual(employee_unit_amount, 16)
        employee_total_works = self.employee.total_works()
        self.assertEqual(employee_total_works, 6)

    def test_send_mail_correct_data_without_old_analytic_line(self):
        employee_real_hours = self.employee.total_real_hours()
        self.assertEqual(employee_real_hours, 22)
        employee_unit_amount = self.employee.total_unit_amount()
        self.assertEqual(employee_unit_amount, 16)
        employee_total_works = self.employee.total_works()
        self.assertEqual(employee_total_works, 6)
        self.employee.send_mail()
        self.assertIn('Dear Employee', self.employee.message_ids[0].body)
        self.assertIn('Tasks completed: %s' % (
            employee_total_works), self.employee.message_ids[0].body)
        self.assertIn(
            'Hours (effective / real): <strong>%s</strong> /'
            ' <strong>%s</strong>' % (
                '%.2f' % employee_unit_amount, '%.2f' % employee_real_hours),
            self.employee.message_ids[0].body)
