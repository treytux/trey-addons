###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPortalCreateTask(HttpCase):

    def setUp(self):
        super().setUp()
        self.portal_user = self.env['res.users'].create({
            'name': 'Portal Test User',
            'login': 'portal_test_user',
            'password': 'portal_test_password',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.portal_partner = self.portal_user.partner_id
        self.project_accessible = self.env['project.project'].create({
            'name': 'Accesible Project',
            'privacy_visibility': 'portal',
        })
        self.project_accessible.message_subscribe(partner_ids=[self.portal_partner.id])
        self.project_private = self.env['project.project'].create({
            'name': 'Private Project',
            'privacy_visibility': 'followers',
        })

    def _get_csrf_token(self, url):
        response = self.url_open(url)
        match = re.search(r'name="csrf_token" value="(.*?)"', response.text)
        return match.group(1) if match else ''

    def test_get_valid_shows_form(self):
        self.authenticate('portal_test_user', 'portal_test_password')
        url = f'/my/projects/{self.project_accessible.id}/task/new'
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="name"', response.text)
        self.assertIn('name="description"', response.text)

    def test_unauthorized_access_redirects(self):
        self.authenticate('portal_test_user', 'portal_test_password')
        url = f'/my/projects/{self.project_private.id}/task/new'
        response = self.url_open(url)
        self.assertTrue(response.url.endswith('/my/projects'))

    def test_post_without_name_shows_error_and_does_not_create(self):
        self.authenticate('portal_test_user', 'portal_test_password')
        url = f'/my/projects/{self.project_accessible.id}/task/new'
        Task = self.env['project.task'].sudo()
        tasks_before = Task.search_count([(
            'project_id', '=', self.project_accessible.id)])
        csrf_token = self._get_csrf_token(url)
        response = self.url_open(url, data={
            'csrf_token': csrf_token,
            'name': '   ',
            'description': 'Test Description',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Name is required.', response.text)
        tasks_after = Task.search_count([(
            'project_id', '=', self.project_accessible.id)])
        self.assertEqual(tasks_before, tasks_after)

    def test_post_valid_creates_task_and_redirects(self):
        self.authenticate('portal_test_user', 'portal_test_password')
        url = f'/my/projects/{self.project_accessible.id}/task/new'
        csrf_token = self._get_csrf_token(url)
        Task = self.env['project.task'].sudo()
        response = self.url_open(url, data={
            'csrf_token': csrf_token,
            'name': 'Success Test Task',
            'description': 'New Task Description',
        })
        self.assertTrue(response.url.endswith(
            f'/my/projects/{self.project_accessible.id}'))
        new_task = Task.search([
            ('project_id', '=', self.project_accessible.id),
            ('name', '=', 'Success Test Task'),
        ], limit=1)
        self.assertTrue(new_task, "The task should have been created in the DB .")
        self.assertIn('New Task Description', str(new_task.description))
        self.assertEqual(new_task.partner_id.id, self.portal_partner.id)
        self.assertFalse(new_task.user_ids, "user_ids must be False (empty list).")
