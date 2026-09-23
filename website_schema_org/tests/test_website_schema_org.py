###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase


class TestWebsiteSchemaOrg(HttpCase):
    def setUp(self):
        super().setUp()
        self.website = self.env['website'].browse(1)

    def test_status_page(self):
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200, msg="page not loaded")

    def test_schema_get(self):
        response = self.url_open('/')
        self.assertIn(bytes(self.website.schema_get(), 'utf-8'),
                      response.content, msg="schema not loaded")
