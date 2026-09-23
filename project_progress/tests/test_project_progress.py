###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectProgress(TransactionCase):

    def _timesheet_create(self, task, hours):
        return task.timesheet_ids.create({
            'name': 'Timesheet sample',
            'account_id': task.project_id.analytic_account_id.id,
            'task_id': task.id,
            'user_id': self.env.user.id,
            'date': '2024-01-01',
            'unit_amount': hours,
        })

    def test_project_progress(self):
        project = self.env['project.project'].create({
            'name': 'Project Test',
        })
        self.assertEqual(len(project.task_ids), 0)
        self.assertEqual(project.progress, 0)
        task_1 = project.task_ids.create({
            'name': 'Task 2',
            'project_id': project.id,
            'planned_hours': 10,
        })
        self.assertEqual(project.progress, 0)
        self._timesheet_create(task_1, 5)
        self.assertEqual(project.progress, 50)
        self._timesheet_create(task_1, 10)
        self.assertEqual(project.progress, 100)
        task_2 = project.task_ids.create({
            'name': 'Task 2',
            'project_id': project.id,
            'planned_hours': 10,
        })
        self.assertEqual(project.progress, 50)
        self._timesheet_create(task_2, 5)
        self.assertEqual(project.progress, 75)
        self._timesheet_create(task_2, 15)
        self.assertEqual(project.progress, 100)
