###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import openerp


class TestGoogleShopping(openerp.tests.HttpCase):
    def setUp(self):
        super(TestGoogleShopping, self).setUp()

    def test_cache_feed(self):
        url = '/google-shopping.xml'
        page = self.url_open(url)
        code = page.getcode()
        self.assertIn(
            code,
            range(200, 300),
            'Fetching %s returned error response (%d)' % (url, code))
        page = self.url_open(url)
        code = page.getcode()
        self.assertIn(
            code,
            range(200, 300),
            'Fetching %s returned error response (%d)' % (url, code))
        website_id = self.ref('website.default_website')
        website = self.env['website'].browse(website_id)
        google_feed_expiry_time = website.google_feed_expiry_time
        website.write({'google_feed_expiry_time': 0})
        self.env.cr.commit()
        page = self.url_open(url)
        code = page.getcode()
        self.assertIn(
            code,
            range(200, 300),
            'Fetching %s returned error response (%d)' % (url, code))
        website.write({'google_feed_expiry_time': google_feed_expiry_time})
        self.env.cr.commit()
