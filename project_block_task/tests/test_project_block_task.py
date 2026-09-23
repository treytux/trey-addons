###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProjectBlockTask(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['hr.employee'].create({
            'name': 'Test employee',
            'user_id': self.env.user.id,
        })
        self.project = self.env['project.project'].create({
            'name': 'Blockable project',
            'allow_timesheets': True,
        })
        self.task = self.env['project.task'].create({
            'name': 'Task 1',
            'project_id': self.project.id,
        })

    def _add_timesheet(self):
        return self.env['account.analytic.line'].create({
            'name': 'Work',
            'project_id': self.project.id,
            'task_id': self.task.id,
            'unit_amount': 1.0,
        })

    def test_timesheet_allowed_when_not_blocked(self):
        self.assertFalse(self.task.timesheet_blocked)
        self.assertTrue(self._add_timesheet())

    def test_blocked_by_kanban_state(self):
        self.task.kanban_state = 'blocked'
        self.assertTrue(self.task.timesheet_blocked)
        with self.assertRaises(ValidationError):
            self._add_timesheet()

    def test_blocked_by_project_flag(self):
        self.project.block_timesheet = True
        self.assertTrue(self.task.timesheet_blocked)
        with self.assertRaises(ValidationError):
            self._add_timesheet()

    def test_blocked_by_archived_project(self):
        self.project.active = False
        self.assertTrue(self.task.timesheet_blocked)
        with self.assertRaises(ValidationError):
            self._add_timesheet()

    def test_unblock_restores_registration(self):
        self.task.kanban_state = 'blocked'
        self.task.kanban_state = 'normal'
        self.assertFalse(self.task.timesheet_blocked)
        self.assertTrue(self._add_timesheet())

    def test_compute_without_project_stages_group(self):
        group = self.env.ref('project.group_project_stages')
        user = self.env['res.users'].create({
            'name': 'Timesheet user',
            'login': 'timesheet_user',
            'groups_id': [
                (4, self.env.ref('project.group_project_user').id),
                (4, self.env.ref('hr_timesheet.group_hr_timesheet_user').id),
                (3, group.id),
            ],
        })
        task = self.task.with_user(user)
        self.assertFalse(task.timesheet_blocked)
        self.project.block_timesheet = True
        self.assertTrue(task.timesheet_blocked)
