###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestWebsiteGoogleTranslateTemplate(TransactionCase):

    def test_google_translate_template_renders_widget_attributes(self):
        website = self.env['website'].get_current_website()
        content = self.env['ir.ui.view']._render_template(
            'website_google_translate.google_translate_element',
            {'website': website})
        self.assertIn('id="google_translate_element"', content)
        self.assertIn('class="wgt_widget"', content)
        self.assertIn(
            'data-page-language="%s"'
            % website.default_lang_id.code.split('_')[0], content)
        included_languages = ','.join(
            language.code.split('_')[0] for language in website.language_ids)
        self.assertIn(
            'data-included-languages="%s"' % included_languages, content)
