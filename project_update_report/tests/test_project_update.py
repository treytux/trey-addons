###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectProject(TransactionCase):
    def setUp(self):
        super().setUp()
        user = self.env['res.users'].create({
            'name': 'New user test',
            'login': 'newtest',
            'email': 'newuser@test.com',
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.project_A = self.env['project.project'].create({
            'name': 'project_A',
            'partner_id': partner.id,
        })
        self.project_update_1 = self.env['project.update'].create({
            'name': "Test Project Update",
            'project_id': self.project_A.id,
            'status': 'at_risk',
            'user_id': user.id,
        })

    def test_context_mail(self):
        wizard = self.project_update_1.send_update_report()
        self.assertEqual(wizard['context']['default_model'], 'project.update')
        self.assertEqual(wizard['context']['default_res_id'], self.project_update_1.id)
        self.assertTrue(wizard['context']['default_use_template'])
