###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase


class TestWebsiteSchemaOrg(HttpCase):
    def setUp(self):
        super().setUp()
        self.page = self.env['website.page'].browse(4)

    def test_status_page(self):
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200, msg="page not loaded")

    def test_schema_get(self):
        response = self.url_open('/')
        self.assertIn(bytes(self.page.website_id.schema_get(), 'utf-8'),
                      response.content, msg="schema not loaded")
