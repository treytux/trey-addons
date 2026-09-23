###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

import odoo.tests
from odoo import Command, fields
from odoo.addons.portal_project.controllers import main as portal_main


class TestPortalProject(odoo.tests.TransactionCase):

    def setUp(self):
        super().setUp()
        self.portal_controller = portal_main.CustomerPortal()
        self.portal_user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Portal Project Search User',
                'login': 'portal_project_search_user',
                'email': 'portal_project_search_user@example.com',
                'password': 'portal_project_search_user',
                'groups_id': [
                    Command.set([self.env.ref('base.group_portal').id])
                ],
            })
        self.partner_match = self.env['res.partner'].create({
            'name': 'Portal Project Search Partner',
            'email': 'portal_project_search_partner@example.com',
        })
        self.partner_other = self.env['res.partner'].create({
            'name': 'Portal Project Other Partner',
            'email': 'portal_project_other_partner@example.com',
        })
        self.project_match = self.env['project.project'].sudo().create({
            'name': 'Portal Project Alpha Name',
            'description': 'Portal Project Alpha Description',
            'partner_id': self.partner_match.id,
            'user_id': self.portal_user.id,
        })
        self.project_other = self.env['project.project'].sudo().create({
            'name': 'Portal Project Beta Name',
            'description': 'Portal Project Beta Description',
            'partner_id': self.partner_other.id,
        })
        self.env['project.milestone'].sudo().create({
            'name': 'Portal Project Alpha Milestone',
            'project_id': self.project_match.id,
        })
        self.project_match.message_post(body='Portal Project Alpha Message')

    def _search_project_ids(self, domain):
        return self.env['project.project'].sudo().search(domain).ids

    def test_project_get_search_domain(self):
        fake_request = type('Request', (), {'env': self.env})
        with patch.object(portal_main, 'request', fake_request):
            domain_content = self.portal_controller._project_get_search_domain(
                'content', 'Alpha Name')
            domain_customer = self.portal_controller._project_get_search_domain(
                'customer', 'Search Partner')
            domain_message = self.portal_controller._project_get_search_domain(
                'message', 'Alpha Message')
            domain_ref = self.portal_controller._project_get_search_domain(
                'ref', str(self.project_match.id))
            domain_milestone = (
                self.portal_controller._project_get_search_domain(
                    'milestone', 'Alpha Milestone'))
            domain_users = self.portal_controller._project_get_search_domain(
                'users', 'Search User')
        self.assertIn(
            self.project_match.id, self._search_project_ids(domain_content))
        self.assertNotIn(
            self.project_other.id, self._search_project_ids(domain_content))
        self.assertIn(
            self.project_match.id, self._search_project_ids(domain_customer))
        self.assertNotIn(
            self.project_other.id, self._search_project_ids(domain_customer))
        self.assertIn(
            self.project_match.id, self._search_project_ids(domain_message))
        self.assertNotIn(
            self.project_other.id, self._search_project_ids(domain_message))
        self.assertIn(
            self.project_match.id, self._search_project_ids(domain_ref))
        self.assertIn(
            self.project_match.id, self._search_project_ids(domain_milestone))
        self.assertNotIn(
            self.project_other.id, self._search_project_ids(domain_milestone))
        self.assertIn(
            self.project_match.id, self._search_project_ids(domain_users))
        self.assertNotIn(
            self.project_other.id, self._search_project_ids(domain_users))

    def test_get_year_searchbar_filters(self):
        searchbar_filters, year_to = (
            self.portal_controller.get_year_searchbar_filters(
                '2024-01-15 00:00:00', '2023-01-01 00:00:00'))
        self.assertIn('active_tasks', searchbar_filters)
        self.assertEqual(
            searchbar_filters['active_tasks']['domain'],
            [
                ('task_id.is_closed', '=', False),
                '|',
                ('task_id.stage_id', '=', False),
                ('task_id.stage_id.name', 'not in',
                 self.portal_controller._closed_task_stage_names),
            ])
        self.assertIn('all', searchbar_filters)
        self.assertEqual(searchbar_filters['all']['domain'], [])
        self.assertEqual(
            searchbar_filters['2024']['domain'][0],
            ('date', '>=', fields.Datetime.from_string('2024-01-01 00:00:00')))
        self.assertEqual(
            searchbar_filters['2024']['domain'][1],
            ('date', '<=', fields.Datetime.from_string('2024-12-31 23:59:59')))
        self.assertIn(str(year_to), searchbar_filters)

    def test_active_task_domain_excludes_closed_stage_names(self):
        stage_open = self.env['project.task.type'].sudo().create({
            'name': 'En curso',
            'fold': False,
            'project_ids': [Command.link(self.project_match.id)],
        })
        stage_done = self.env['project.task.type'].sudo().create({
            'name': 'Done',
            'fold': False,
            'project_ids': [Command.link(self.project_match.id)],
        })
        stage_cancelled = self.env['project.task.type'].sudo().create({
            'name': 'Cancelled',
            'fold': False,
            'project_ids': [Command.link(self.project_match.id)],
        })
        task_open = self.env['project.task'].sudo().create({
            'name': 'Portal Project Active Domain Open',
            'project_id': self.project_match.id,
            'stage_id': stage_open.id,
        })
        task_done = self.env['project.task'].sudo().create({
            'name': 'Portal Project Active Domain Done',
            'project_id': self.project_match.id,
            'stage_id': stage_done.id,
        })
        task_cancelled = self.env['project.task'].sudo().create({
            'name': 'Portal Project Active Domain Cancelled',
            'project_id': self.project_match.id,
            'stage_id': stage_cancelled.id,
        })
        active_tasks = self.env['project.task'].sudo().with_context(
            lang='es_ES',
        ).search([
            ('id', 'in', (task_open | task_done | task_cancelled).ids),
        ] + self.portal_controller._get_active_task_domain())
        self.assertIn(task_open, active_tasks)
        self.assertNotIn(task_done, active_tasks)
        self.assertNotIn(task_cancelled, active_tasks)

    def test_view_on_portal(self):
        action = self.project_match.view_on_portal()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['target'], 'self')
        self.assertEqual(
            action['url'], '/my/project/%s' % self.project_match.id)
