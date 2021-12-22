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
        self.employee1 = self.env['hr.employee'].create({
            'name': 'Employee1',
        })
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Employee2',
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
                    'employee_id': self.employee1.id,
                }),
                (0, 0, {
                    'name': 'First line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 2,
                    'real_time': 3,
                    'employee_id': self.employee1.id,
                }),
                (0, 0, {
                    'name': 'Second line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee1.id,
                }),
                (0, 0, {
                    'name': 'Other line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee1.id,
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
                    'employee_id': self.employee1.id,
                }),
                (0, 0, {
                    'name': 'First line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 2,
                    'real_time': 3,
                    'employee_id': self.employee1.id,
                }),
                (0, 0, {
                    'name': 'Second line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee1.id,
                }),
                (0, 0, {
                    'name': 'Other line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 4,
                    'employee_id': self.employee1.id,
                }),
            ],
        })
        self.task3 = self.env['project.task'].create({
            'name': 'Test task3',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'name': 'Old line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=3),
                    'unit_amount': 3,
                    'real_time': 3,
                    'employee_id': self.employee2.id,
                }),
                (0, 0, {
                    'name': 'First line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 2,
                    'real_time': 3,
                    'employee_id': self.employee2.id,
                }),
                (0, 0, {
                    'name': 'Second line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 3,
                    'employee_id': self.employee2.id,
                }),
                (0, 0, {
                    'name': 'Other line',
                    'account_id': self.account.id,
                    'date': datetime.today() - relativedelta(months=1),
                    'unit_amount': 3,
                    'real_time': 3,
                    'employee_id': self.employee2.id,
                }),
            ],
        })

    def test_correct_quantity_hours(self):
        employee_real_hours = self.employee1.total_real_hours()
        self.assertEqual(employee_real_hours, 22)
        employee_unit_amount = self.employee1.total_unit_amount()
        self.assertEqual(employee_unit_amount, 16)
        employee_total_works = self.employee1.total_works()
        self.assertEqual(employee_total_works, 6)

    def test_send_mail_correct_data_without_old_analytic_line(self):
        employee_real_hours = self.employee1.total_real_hours()
        self.assertEqual(employee_real_hours, 22)
        employee_unit_amount = self.employee1.total_unit_amount()
        self.assertEqual(employee_unit_amount, 16)
        employee_total_works = self.employee1.total_works()
        self.assertEqual(employee_total_works, 6)
        self.employee1.send_mail()
        self.assertIn('Dear Employee1', self.employee1.message_ids[0].body)
        self.assertIn('Total tasks - <strong>%s</strong>' % (
            employee_total_works), self.employee1.message_ids[0].body)
        self.assertIn('Total hours - <strong>%s</strong>' % (
            employee_unit_amount),
            self.employee1.message_ids[0].body)
        self.assertIn('Total real hours - <strong>%s</strong>' % (
            employee_real_hours),
            self.employee1.message_ids[0].body)
        self.employee2.send_mail()
        self.assertIn('Dear Employee2', self.employee2.message_ids[0].body)
        self.assertIn('Total tasks - <strong>%s</strong>' % (
            self.employee2.total_works()), self.employee2.message_ids[0].body)
        self.assertIn('Total hours - <strong>%s</strong>' % (
            self.employee2.total_unit_amount()),
            self.employee2.message_ids[0].body)
        self.assertIn('Total real hours - <strong>%s</strong>' % (
            self.employee2.total_real_hours()),
            self.employee2.message_ids[0].body)
