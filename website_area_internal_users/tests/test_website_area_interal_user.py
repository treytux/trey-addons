###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase


class TestWebsitePage(HttpCase):

    def setUp(self):
        super().setUp()
        self.page = self.env.ref('website.contactus_page')
        self.endpoint = '/contactus'
        self.user_internal = self.env['res.users'].create({
            'name': 'Employee',
            'login': 'internal',
            'password': 'internal',
            'groups_id': [(4, self.env.ref('base.group_user').id)],
        })

    def test_visible_internal_only_public(self):
        self.page.is_visible = True
        self.assertTrue(self.page.is_visible)
        self.page.internal_only = True
        self.assertEqual(self.url_open(url=self.endpoint).status_code, 404)

    def test_visible_internal_only_portal(self):
        self.page.is_visible = True
        self.assertTrue(self.page.is_visible)
        self.page.internal_only = True
        self.authenticate('portal', 'portal')
        self.assertEqual(self.url_open(url=self.endpoint).status_code, 404)

    def test_visible_internal_only_employee(self):
        self.page.is_visible = True
        self.assertTrue(self.page.is_visible)
        self.page.internal_only = True
        self.authenticate('internal', 'internal')
        self.assertEqual(self.url_open(url=self.endpoint).status_code, 200)
