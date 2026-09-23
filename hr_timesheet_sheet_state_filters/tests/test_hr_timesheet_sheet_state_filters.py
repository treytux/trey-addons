from datetime import date, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestAnalyticAccountBalance(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({
            'name': 'Project Test',
        })
        self.account = self.env['account.analytic.account'].create({
            'name': 'Account A',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Employee A',
            'user_id': self.env.user.id,
        })
        self.task = self.env['project.task'].create({
            'name': 'Task Test',
            'project_id': self.project.id,
        })

    def test_compute_debit_credit_balance_filters_correct_lines(self):
        AnalyticLine = self.env['account.analytic.line']
        AnalyticLine.create({
            'name': 'Valid line',
            'account_id': self.account.id,
            'amount': 100.0,
            'sheet_state': 'done',
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        AnalyticLine.create({
            'name': 'In Draft Line',
            'account_id': self.account.id,
            'amount': 200.0,
            'sheet_state': 'draft',
            'sheet_id': False,
            'task_id': self.env['project.task'].create({
                'name': 'Task',
                'project_id': self.env['project.project'].create({
                    'name': 'Project',
                }).id,
            }).id,
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        AnalyticLine.create({
            'name': 'Invalid Line',
            'account_id': self.account.id,
            'amount': 300.0,
            'sheet_state': 'draft',
            'sheet_id': self.env['hr_timesheet.sheet'].create({
                'name': 'Sheet',
                'employee_id': self.employee.id,
            }).id,
            'task_id': self.env['project.task'].create({
                'name': 'Task',
                'project_id': self.env['project.project'].create({
                    'name': 'Project',
                }).id,
            }).id,
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        self.account._compute_debit_credit_balance()
        self.assertEqual(self.account.credit, 100.0)
        self.assertEqual(self.account.debit, 0.0)
        self.assertEqual(self.account.balance, 100.0)

    def test_effective_hours_by_sheet_state(self):
        AnalyticLine = self.env['account.analytic.line']
        sheet_done = self.env['hr_timesheet.sheet'].create({
            'name': 'Sheet Done',
            'employee_id': self.employee.id,
            'date_start': date(2020, 1, 1),
            'date_end': date(2020, 1, 7),
        })
        sheet_draft = self.env['hr_timesheet.sheet'].create({
            'name': 'Sheet Draft',
            'employee_id': self.employee.id,
            'date_start': date(2020, 2, 1),
            'date_end': date(2020, 2, 7),
        })
        aprove_line_1 = AnalyticLine.create({
            'name': 'Done 1',
            'unit_amount': 2.0,
            'task_id': self.task.id,
            'sheet_id': sheet_done.id,
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        aprove_line_1.write({'sheet_id': sheet_done.id})
        aprove_line_2 = AnalyticLine.create({
            'name': 'Done 2',
            'unit_amount': 3.0,
            'task_id': self.task.id,
            'sheet_id': sheet_done.id,
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        aprove_line_2.write({'sheet_id': sheet_done.id})
        no_aprove_line = AnalyticLine.create({
            'name': 'Draft',
            'unit_amount': 5.0,
            'task_id': self.task.id,
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        no_aprove_line.write({'sheet_id': sheet_draft.id})
        sheet_done.action_timesheet_confirm()
        sheet_done.action_timesheet_done()
        self.task._compute_effective_hours_by_state()
        self.assertEqual(self.task.effective_hours, 10.0)
        self.assertEqual(self.task.effective_hours_approve, 5.0)
        self.assertEqual(self.task.effective_hours_pending, 5.0)

    def test_timesheet_analysis_report(self):
        self.env['account.analytic.line'].search([]).unlink()
        new_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_%s' % fields.Datetime.now().timestamp(),
            'email': 'test@example.com',
        })
        employee2 = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'user_id': new_user.id,
        })
        project_billable = self.env['project.project'].create({
            'name': 'Billable Project',
            'allow_billable': True,
        })
        project_non_billable = self.env['project.project'].create({
            'name': 'Non Billable Project',
            'allow_billable': False,
        })
        sheet_approved = self.env['hr_timesheet.sheet'].create({
            'employee_id': self.employee.id,
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + timedelta(days=7),
        })
        sheet_draft = self.env['hr_timesheet.sheet'].create({
            'employee_id': employee2.id,
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + timedelta(days=7),
        })
        self.env['account.analytic.line'].create({
            'name': 'Billable approved line',
            'project_id': project_billable.id,
            'sheet_id': sheet_approved.id,
            'unit_amount': 5.0,
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        self.env['account.analytic.line'].create({
            'name': 'Non-billable approved line',
            'project_id': project_non_billable.id,
            'sheet_id': sheet_approved.id,
            'unit_amount': 3.0,
            'employee_id': self.employee.id,
            'date': fields.Date.today(),
        })
        self.env['account.analytic.line'].create({
            'name': 'Billable draft line',
            'project_id': project_billable.id,
            'sheet_id': sheet_draft.id,
            'unit_amount': 2.0,
            'employee_id': employee2.id,
            'date': fields.Date.today(),
        })
        sheet_approved.action_timesheet_confirm()
        sheet_approved.action_timesheet_done()
        Report = self.env['timesheets.analysis.report']
        self.assertIn('sheet_state', Report._fields)
        self.assertIn('billable_project', Report._fields)

    def test_report_project_task_user_values(self):
        Report = self.env['report.project.task.user']
        self.assertIn(
            'hours_effective_pending', Report._fields,
            'The field hours_effective_pending does not exist in the report'
        )
        self.assertIn(
            'hours_effective_approve', Report._fields,
            'The field hours_effective_approve does not exist in the report'
        )
