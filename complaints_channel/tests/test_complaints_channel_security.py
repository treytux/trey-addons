###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestComplaintsChannelSecurity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.complaint = self.env['complaints.channel'].create({
            'email': 'test@test.com',
            'company': self.company.id,
            'people_involved': 'Test Involved',
            'witnesses': 'Test Witness',
            'reportable_facts': 'Test Fact',
            'start_date': date.today(),
            'description': 'Test Description',
        })

    def _create_user(self, login, group_xml_ids):
        group_ids = []
        for xml_id in group_xml_ids:
            group = self.env.ref(xml_id)
            group_ids.append(group.id)
        return self.env['res.users'].create({
            'name': login,
            'login': login,
            'password': login,
            'groups_id': [(6, 0, group_ids)],
        })

    def test_manager_permissions(self):
        manager = self._create_user(
            'manager', ['complaints_channel.group_complaint_manager'])
        complaints = self.env['complaints.channel'].with_user(
            manager).search([])
        self.assertIn(self.complaint, complaints)
        new_complaint = self.env['complaints.channel'].with_user(
            manager).create({
                'email': 'test@test.com',
                'company': self.company.id,
                'people_involved': 'Test Involved',
                'witnesses': 'Test Witness',
                'reportable_facts': 'Test Fact',
                'start_date': date.today(),
                'description': 'Test Description',
            })
        self.assertTrue(new_complaint)
        new_complaint.with_user(manager).write({'email': 'manager@test.com'})
        self.assertEqual(new_complaint.email, 'manager@test.com')
        new_complaint.with_user(manager).unlink()
        self.assertFalse(self.env['complaints.channel'].search([
            ('id', '=', new_complaint.id),
        ]))

    def test_user_permissions(self):
        user = self._create_user(
            'user', ['complaints_channel.group_complaint_user'])
        complaints = self.env['complaints.channel'].with_user(user).search([])
        self.assertIn(self.complaint, complaints)
        with self.assertRaises(AccessError):
            self.env['complaints.channel'].with_user(user).create({
                'email': 'user@test.com',
                'company': self.company.id,
                'people_involved': 'Test Involved',
                'witnesses': 'Test Witness',
                'reportable_facts': 'Test Fact',
                'start_date': date.today(),
                'description': 'Test Description',
            })
        with self.assertRaises(AccessError):
            self.complaint.with_user(user).write({
                'email': 'user@test.com',
            })
        with self.assertRaises(AccessError):
            self.complaint.with_user(user).unlink()

    def test_no_group_permissions(self):
        nobody = self._create_user('nobody', [])
        with self.assertRaises(AccessError):
            self.env['complaints.channel'].with_user(nobody).search([])
        with self.assertRaises(AccessError):
            self.env['complaints.channel'].with_user(nobody).create({
                'email': 'user@test.com',
                'company': self.company.id,
                'people_involved': 'Test Involved',
                'witnesses': 'Test Witness',
                'reportable_facts': 'Test Fact',
                'start_date': date.today(),
                'description': 'Test Description',
            })
        with self.assertRaises(AccessError):
            self.complaint.with_user(nobody).write({
                'email': 'user@test.com',
            })
        with self.assertRaises(AccessError):
            self.complaint.with_user(nobody).unlink()
