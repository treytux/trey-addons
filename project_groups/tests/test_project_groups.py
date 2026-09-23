###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectGroups(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['ir.sequence'].create({
            'name': 'Project Group Status Sequence',
            'code': 'project.group.status',
            'implementation': 'standard',
            'padding': 3,
            'number_increment': 1,
            'number_next': 1,
        })
        self.status1 = self.env['project.group.status'].create({
            'name': 'Closed',
            'is_closed': True,
        })
        self.status2 = self.env['project.group.status'].create({
            'name': 'Open',
        })
        self.group = self.env['project.group'].create({
            'name': 'Test Group',
            'project_group_status': self.status1.id,
        })

    def test_auto_assign_sequence(self):
        self.assertNotEqual(self.status1.status_sequence, 0)
        self.assertNotEqual(self.status2.status_sequence, 0)
        self.assertEqual(self.status1.status_sequence, 1)
        self.assertEqual(self.status2.status_sequence, 2)

    def test_do_next_status(self):
        self.group.do_next_status()
        self.assertEqual(self.group.project_group_status, self.status2)

    def test_cancel_project_group(self):
        group2 = self.env['project.group'].create({
            'name': 'Test Group',
            'project_group_status': self.status2.id,
        })
        group2.cancel_project_group()
        self.assertEqual(group2.project_group_status, self.status1)

    def test_reopen_project_group(self):
        self.assertEqual(self.group.project_group_status, self.status1)
        self.group.reopen_project_group()
        status_open = self.env.ref('project_groups.project_group_status_open')
        self.assertEqual(self.group.project_group_status, status_open)

    def test_project_count(self):
        self.env['project.project'].create({
            'name': 'Test Project 1',
            'project_group_id': self.group.id,
        })
        self.env['project.project'].create({
            'name': 'Test Project 2',
            'project_group_id': self.group.id,
        })
        self.env['project.project'].create({
            'name': 'Test Project 3',
            'project_group_id': self.group.id,
        })
        self.assertEqual(self.group.project_count, 3)

    def test_action_view_project(self):
        project_a = self.env['project.project'].create({
            'name': 'Project A',
            'project_group_id': self.group.id,
        })
        project_b = self.env['project.project'].create({
            'name': 'Project B',
            'project_group_id': self.group.id,
        })
        action = self.group.action_view_project()
        self.assertIn('domain', action)
        self.assertEqual(len(action['domain'][0][2]), 2)
        project_b.unlink()
        action = self.group.action_view_project()
        self.assertEqual(action['res_id'], project_a.id)
        self.assertEqual(action['views'][0][1], 'form')

    def test_multi_company_security(self):
        other_company = self.env['res.company'].create({
            'name': 'Other Company',
        })
        other_user = self.env['res.users'].create({
            'name': 'Other User',
            'login': 'other_user',
            'email': 'other@test.com',
            'company_id': other_company.id,
            'company_ids': [(4, other_company.id)],
            'groups_id': [(4, self.env.ref('project.group_project_user').id)],
        })
        self.group.company_id = self.env.company.id
        group_ids = self.env['project.group'].with_user(other_user).search([
            ('id', '=', self.group.id),
        ])
        self.assertFalse(group_ids)
