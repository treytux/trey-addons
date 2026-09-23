###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from urllib.parse import urlparse

import odoo.tests
from odoo import Command, fields, http


@odoo.tests.tagged('post_install', '-at_install')
class TestPortalProjectHttp(odoo.tests.HttpCase):

    def setUp(self):
        super().setUp()
        self.portal_login = 'portal_project_http_user'
        self.portal_password = 'portal_project_http_user'
        self.portal_user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Portal Project HTTP User',
                'login': self.portal_login,
                'email': 'portal_project_http_user@example.com',
                'password': self.portal_password,
                'groups_id': [
                    Command.set([self.env.ref('base.group_portal').id])
                ],
            })
        self.other_partner = self.env['res.partner'].create({
            'name': 'Portal Project HTTP Other Partner',
            'email': 'portal_project_http_other_partner@example.com',
        })
        self.project_portal = self.env['project.project'].sudo().create({
            'name': 'Portal Project HTTP Main',
            'partner_id': self.portal_user.partner_id.id,
            'allow_timesheets': True,
            'unit_balance_display': 'real',
            'privacy_visibility': 'portal',
        })
        self.project_other = self.env['project.project'].sudo().create({
            'name': 'Portal Project HTTP Hidden',
            'partner_id': self.other_partner.id,
            'allow_timesheets': True,
            'unit_balance_display': 'real',
            'privacy_visibility': 'portal',
        })
        self.project_portal.message_subscribe(
            partner_ids=[self.portal_user.partner_id.id])
        self.task_open = self.env['project.task'].sudo().create({
            'name': 'Portal Project HTTP Task Open',
            'project_id': self.project_portal.id,
        })
        self.stage_done = self.env['project.task.type'].sudo().create({
            'name': 'Done',
            'fold': False,
            'project_ids': [Command.link(self.project_portal.id)],
        })
        self.task_done = self.env['project.task'].sudo().create({
            'name': 'Portal Project HTTP Task Done',
            'project_id': self.project_portal.id,
            'stage_id': self.stage_done.id,
        })
        self.task_previous_year = self.env['project.task'].sudo().create({
            'name': 'Portal Project HTTP Task Old Date',
            'project_id': self.project_portal.id,
        })
        self.task_other = self.env['project.task'].sudo().create({
            'name': 'Portal Project HTTP Task Other',
            'project_id': self.project_other.id,
        })
        self.employee = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not self.employee:
            self.employee = self.env['hr.employee'].sudo().create({
                'name': 'Portal Project HTTP Employee',
                'user_id': self.env.user.id,
                'company_id': self.env.company.id,
            })
        current_year = fields.Date.today().year
        self.current_year = current_year
        self.previous_year = current_year - 1
        self.env.cr.execute(
            """
            UPDATE project_task
               SET create_date = %s
             WHERE id = %s
            """,
            ('%s-12-04 10:00:00' % self.previous_year,
             self.task_previous_year.id))
        self.task_previous_year.invalidate_recordset(['create_date'])
        self.env['account.analytic.line'].sudo().create({
            'name': 'Portal Project HTTP Timesheet Current',
            'project_id': self.project_portal.id,
            'task_id': self.task_open.id,
            'date': '%s-02-10' % self.current_year,
            'unit_amount': 2.0,
            'employee_id': self.employee.id,
        })
        self.env['account.analytic.line'].sudo().create({
            'name': 'Portal Project HTTP Timesheet Previous',
            'project_id': self.project_portal.id,
            'task_id': self.task_open.id,
            'date': '%s-05-12' % self.previous_year,
            'unit_amount': 4.0,
            'employee_id': self.employee.id,
        })
        self.env['account.analytic.line'].sudo().create({
            'name': 'Portal Project HTTP Timesheet Done',
            'project_id': self.project_portal.id,
            'task_id': self.task_done.id,
            'date': '%s-03-15' % self.current_year,
            'unit_amount': 8.0,
            'employee_id': self.employee.id,
        })
        self.env['account.analytic.line'].sudo().create({
            'name': 'Portal Project HTTP Timesheet Old Date Task',
            'project_id': self.project_portal.id,
            'task_id': self.task_previous_year.id,
            'date': '%s-08-21' % self.current_year,
            'unit_amount': 5.0,
            'employee_id': self.employee.id,
        })
        self.env['account.analytic.line'].sudo().create({
            'name': 'Portal Project HTTP Timesheet Other Project',
            'project_id': self.project_other.id,
            'task_id': self.task_other.id,
            'date': '%s-01-15' % self.current_year,
            'unit_amount': 9.0,
            'employee_id': self.employee.id,
        })
        self.project_portal._portal_ensure_token()
        self.project_other._portal_ensure_token()

    def _authenticate_portal_user(self):
        self.authenticate(self.portal_login, self.portal_password)
        http.root.session_store.save(self.session)

    def _assert_redirect_path(self, response, expected_path):
        location = response.headers.get('Location')
        self.assertTrue(location)
        if location.startswith('http'):
            self.assertEqual(urlparse(location).path, expected_path)
        else:
            self.assertEqual(location, expected_path)

    def _assert_response_contains(self, response, text):
        self.assertTrue(
            text in response.text, '%s not found in response' % text)

    def _assert_response_not_contains(self, response, text):
        self.assertFalse(text in response.text, '%s found in response' % text)

    def test_portal_my_project_computes_periods_and_graph_data(self):
        self._authenticate_portal_user()
        response = self.url_open(
            '/my/projects/%s?filterby=all' % self.project_portal.id)
        self.assertEqual(response.status_code, 200)
        self._assert_response_contains(response, 'js_pp_graph_timesheets')
        self._assert_response_contains(response, '&#34;count&#34;: 4.0')
        self._assert_response_contains(response, '&#34;count&#34;: 15.0')
        self._assert_response_contains(
            response, 'Portal Project HTTP Task Done')
        self._assert_response_contains(
            response, 'Portal Project HTTP Task Old Date')
        response = self.url_open(
            '/my/projects/%s?filterby=%s'
            % (self.project_portal.id, self.current_year))
        self.assertEqual(response.status_code, 200)
        self._assert_response_contains(response, 'js_pp_graph_timesheets')
        self._assert_response_contains(response, '&#34;count&#34;: 2.0')
        self._assert_response_contains(response, '&#34;count&#34;: 5.0')
        self._assert_response_contains(response, '&#34;count&#34;: 8.0')
        self._assert_response_contains(
            response, 'Portal Project HTTP Task Done')
        self._assert_response_not_contains(
            response, 'Portal Project HTTP Task Old Date')
        response = self.url_open('/my/projects/%s' % self.project_portal.id)
        self.assertEqual(response.status_code, 200)
        self._assert_response_contains(
            response, 'Portal Project HTTP Task Open')
        self._assert_response_not_contains(
            response, 'Portal Project HTTP Task Done')

    def test_portal_my_project_paginates_tasks_without_default_group(self):
        tasks = self.env['project.task'].sudo().create([{
            'name': 'Portal Project HTTP Page Task %03d' % number,
            'project_id': self.project_portal.id,
        } for number in range(55)])
        self.env['account.analytic.line'].sudo().create([{
            'name': 'Portal Project HTTP Page Timesheet %03d' % number,
            'project_id': self.project_portal.id,
            'task_id': task.id,
            'date': '%s-06-10' % self.current_year,
            'unit_amount': 0.0,
            'employee_id': self.employee.id,
        } for number, task in enumerate(tasks)])
        self._authenticate_portal_user()
        response_page_1 = self.url_open(
            '/my/projects/%s?sortby=name&filterby=%s'
            % (self.project_portal.id, self.current_year))
        response_page_2 = self.url_open(
            '/my/projects/%s/page/2?sortby=name&filterby=%s'
            % (self.project_portal.id, self.current_year))
        self.assertEqual(response_page_1.status_code, 200)
        self.assertEqual(response_page_2.status_code, 200)
        self.assertIn('filterby=%s' % self.current_year, response_page_1.text)
        self.assertIn('Portal Project HTTP Page Task 000', response_page_1.text)
        self.assertNotIn(
            'Portal Project HTTP Page Task 050', response_page_1.text)
        self.assertIn('Portal Project HTTP Page Task 050', response_page_2.text)
        self.assertNotIn(
            'Portal Project HTTP Page Task 000', response_page_2.text)
        self.assertNotIn('name="project_name"', response_page_2.text)

    def test_portal_my_project_redirects_without_project_context(self):
        self._authenticate_portal_user()
        response = self.url_open(
            '/my/projects/%s' % self.project_other.id, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self._assert_redirect_path(response, '/my')

    def test_timesheets_unit_route_respects_access_and_filter(self):
        self._authenticate_portal_user()
        response_ok = self.url_open(
            '/my/unit/timesheets/%s?filterby=%s'
            % (self.project_portal.id, self.current_year))
        self.assertEqual(response_ok.status_code, 200)
        self.assertIn(
            'Portal Project HTTP Timesheet Current', response_ok.text)
        self.assertNotIn(
            'Portal Project HTTP Timesheet Previous', response_ok.text)
        response_forbidden = self.url_open(
            '/my/unit/timesheets/%s' % self.project_other.id,
            allow_redirects=False)
        self.assertEqual(response_forbidden.status_code, 303)
        self._assert_redirect_path(response_forbidden, '/my')

    def test_timesheets_export_returns_xlsx(self):
        self._authenticate_portal_user()
        response = self.url_open(
            '/my/unit/timesheets/%s/export?filterby=all'
            % self.project_portal.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get('Content-Type'),
            'application/vnd.ms-excel')
        self.assertIn(
            'timesheets.xlsx', response.headers.get('Content-Disposition', ''))
        self.assertTrue(response.content.startswith(b'PK\x03\x04'))
