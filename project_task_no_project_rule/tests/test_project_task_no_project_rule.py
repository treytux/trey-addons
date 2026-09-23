###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProjectTaskNoProjectRule(common.TransactionCase):

    def setUp(self):
        super().setUp()
        project_group_id = self.env.ref('project.group_project_user').id
        self.project_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Project User',
            'login': 'project_user_rule@test.com',
            'email': 'project_user_rule@test.com',
            'groups_id': [(6, 0, [project_group_id])],
        })
        self.assigned_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Assigned User',
            'login': 'assigned_user_rule@test.com',
            'email': 'assigned_user_rule@test.com',
            'groups_id': [(6, 0, [project_group_id])],
        })

    def test_rule_exists_with_expected_permissions(self):
        xml_id = 'project_task_no_project_rule.project_task_no_project_rule'
        rule = self.env.ref(xml_id)
        domain = (
            '[(\'project_id\', \'=\', False), (\'parent_id\', \'=\', False), '
            '(\'user_ids\', \'=\', False)]'
        )
        self.assertTrue(rule.active)
        self.assertEqual(rule.model_id.model, 'project.task')
        self.assertEqual(rule.domain_force, domain)
        self.assertTrue(rule.perm_read)
        self.assertTrue(rule.perm_write)
        self.assertTrue(rule.perm_create)
        self.assertTrue(rule.perm_unlink)

    def test_project_user_can_read_task_without_project_parent_or_assignees(self):
        task = self.env['project.task'].sudo().create({
            'name': 'Task without project',
            'project_id': False,
            'parent_id': False,
            'user_ids': [(6, 0, [])],
        })
        tasks = self.env['project.task'].with_user(self.project_user).search([
            ('id', '=', task.id),
        ])
        self.assertEqual(tasks.ids, [task.id])

    def test_project_user_cannot_read_task_without_project_if_assigned(self):
        task = self.env['project.task'].sudo().create({
            'name': 'Task without project but assigned',
            'user_ids': [(6, 0, [self.assigned_user.id])],
        })
        tasks = self.env['project.task'].with_user(self.project_user).search([
            ('id', '=', task.id),
        ])
        self.assertFalse(tasks)

    def test_project_user_cannot_read_subtask_without_project(self):
        parent_task = self.env['project.task'].sudo().create({
            'name': 'Parent task',
        })
        subtask = self.env['project.task'].sudo().create({
            'name': 'Subtask without project',
            'parent_id': parent_task.id,
        })
        tasks = self.env['project.task'].with_user(self.project_user).search([
            ('id', '=', subtask.id),
        ])
        self.assertFalse(tasks)
