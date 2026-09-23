###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProjectTaskRemoveFollower(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.project_a = self.env['project.project'].create({
            'name': 'Project A',
        })
        self.project_b = self.env['project.project'].create({
            'name': 'Project B',
        })
        self.external_partner = self.env['res.partner'].create({
            'name': 'External Partner',
            'email': 'external@example.com',
        })
        self.internal_user = self.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal_user',
            'email': 'internal@test.com',
            'groups_id': [(6, 0, [self.ref('base.group_user'), ])],
            'share': False,
        })
        self.internal_partner = self.internal_user.partner_id
        self.portal_user = self.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal_user',
            'email': 'portal@test.com',
            'groups_id': [(6, 0, [self.ref('base.group_portal')])],
            'share': True,
        })
        self.portal_partner = self.portal_user.partner_id

    def test_message_new_syncs_followers_correctly(self):
        msg_dict = {
            'subject': 'Test Mail',
            'author_id': self.external_partner.id,
            'cc': 'internal@test.com',
            'from': 'external@example.com',
        }
        task = self.env['project.task'].message_new(msg_dict, custom_values={
            'project_id': self.project_a.id,
        })
        cc_partner = self.env['res.partner'].search([
            ('email', '=', 'internal@test.com'),
        ])
        self.assertFalse(task.user_ids)
        self.assertIn(self.external_partner, task.message_partner_ids)
        self.assertIn(cc_partner, task.message_partner_ids)
        expected_partners = self.external_partner | cc_partner
        self.assertEqual(task.message_partner_ids, expected_partners)

    def test_project_change_preserves_assignees(self):
        task = self.env['project.task'].create({
            'name': 'Stay Put Task',
            'project_id': self.project_a.id,
            'user_ids': [(4, self.internal_user.id)],
        })
        task.write({
            'project_id': self.project_b.id,
        })
        self.assertIn(self.internal_partner, task.message_partner_ids)
