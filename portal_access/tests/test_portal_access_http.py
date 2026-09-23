from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPortalAccessHttp(HttpCase):

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].get_current_website()
        self.portal_user = self.env['res.users'].create({
            'name': 'Portal HTTP',
            'login': 'portal_http',
            'password': 'test',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

    def test_routes_redirect_to_404(self):
        self.website.portal_access_scope = 'portal'
        self.authenticate('portal_http', 'test')
        for url in ['/my', '/my/account', '/my/security']:
            response = self.url_open(url, allow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertIn('/404', response.headers.get('Location'))

    def test_routes_work_normally(self):
        self.website.portal_access_scope = False
        self.authenticate('portal_http', 'test')
        for url in ['/my', '/my/account', '/my/security']:
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('/404', response.url)
