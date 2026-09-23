###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebsiteGoogleTranslate(HttpCase):

    def test_widget_is_available_on_homepage(self):
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn('id="google_translate_element"', content)
        self.assertIn('data-page-language=', content)
        self.assertIn('data-included-languages=', content)
