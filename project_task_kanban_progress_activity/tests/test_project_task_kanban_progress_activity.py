###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectTaskKanbanProgressActivity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project_task_obj = self.env['project.task']
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })

    def test_create_positive_remaining_hours(self):
        task = self.project_task_obj.create({
            'name': 'Test Task - Positive',
            'project_id': self.project.id,
            'planned_hours': 10.0,
        })
        self.assertEqual(task.planned_remaining_hours, 10.0)

    def test_create_negative_remaining_hours(self):
        task = self.project_task_obj.create({
            'name': 'Test Task - Negative',
            'project_id': self.project.id,
            'planned_hours': 5.0,
        })
        self.env['account.analytic.line'].create({
            'name': 'Task',
            'project_id': self.project.id,
            'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 10.0,
        })
        self.assertEqual(task.planned_remaining_hours, 0.0)

    def test_write_remaining_hours(self):
        task = self.project_task_obj.create({
            'name': 'Test Task - Mutant',
            'project_id': self.project.id,
            'planned_hours': 8.0,
        })
        self.assertEqual(task.planned_remaining_hours, 8.0)
        self.env['account.analytic.line'].create({
            'name': 'Extra work',
            'project_id': self.project.id,
            'task_id': task.id,
            'employee_id': self.employee.id,
            'unit_amount': 11.5,
        })
        self.assertEqual(task.planned_remaining_hours, 0.0)
        task.write({
            'planned_hours': 15.0,
        })
        self.assertEqual(task.planned_remaining_hours, 3.5)
