###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectTaskMainTechnician(TransactionCase):
    def setUp(self):
        super().setUp()
        user = self.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal.user@test.odoo.com',
            'email': 'internal.user@test.odoo.com',
        })
        self.task = self.env['project.task'].create({
            'name': 'Test Task',
            'user_ids': user.ids,
        })
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
            'main_technical_id': self.env.ref('base.user_root').id,
        })

    def test_onchange_project(self):
        self.task.project_id = self.project
        self.task._onchange_project()
        self.assertEqual(self.task.user_ids, self.project.main_technical_id)
