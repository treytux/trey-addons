###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import HttpCase


class TestGoogleShopping(HttpCase):

    def setUp(self):
        super(TestGoogleShopping, self).setUp()
        self.website = self.env.ref('website.default_website')
        self.company = self.website.company_id
        self.other_company = self.env['res.company'].create({
            'name': 'Other Company',
        })
        self.other_website = self.env['website'].create({
            'name': 'Other Website',
            'company_id': self.other_company.id,
        })

    def _create_product(self, name, default_code=None, **kwargs):
        vals = {
            'name': name,
            'website_id': self.website.id,
            'website_published': True,
            'sale_ok': True,
            'company_id': self.company.id,
        }
        if default_code:
            vals['default_code'] = default_code
        vals.update(kwargs)
        return self.env['product.template'].create(vals)

    def _fetch_feed(self):
        page = self.url_open('/google-shopping.xml')
        self.assertIn(
            page.status_code,
            range(200, 300),
            f'Feed returned error {page.status_code}')
        return page.content.decode('utf-8')

    def test_cache_feed(self):
        url = '/google-shopping.xml'
        page = self.url_open(url)
        self.assertIn(
            page.status_code,
            range(200, 300),
            f'Fetching {url} returned error response ({page.status_code})')
        page = self.url_open(url)
        self.assertIn(
            page.status_code,
            range(200, 300),
            f'Fetching {url} (2nd) returned error response '
            f'({page.status_code})')
        website = self.env.ref('website.default_website')
        original_expiry = website.google_feed_expiry_time
        website.write({'google_feed_expiry_time': 0})
        page = self.url_open(url)
        self.assertIn(
            page.status_code,
            range(200, 300),
            f'Fetching {url} (no cache) returned error response '
            f'({page.status_code})')
        website.write({'google_feed_expiry_time': original_expiry})

    def test_domain_website_id_matches(self):
        self._create_product('Product', default_code='WS-MATCH')
        content = self._fetch_feed()
        self.assertIn(
            'WS-MATCH',
            content,
            'Expected product with matching website_id in feed')

    def test_domain_website_id_false(self):
        self._create_product(
            'Product', default_code='WS-FALSE', website_id=False)
        content = self._fetch_feed()
        self.assertIn(
            'WS-FALSE',
            content,
            'Expected product with website_id=False in feed')

    def test_domain_website_id_other(self):
        self._create_product(
            'Product',
            default_code='WS-OTHER',
            website_id=self.other_website.id)
        content = self._fetch_feed()
        self.assertNotIn(
            'WS-OTHER',
            content,
            'Product with other website_id should NOT appear in feed')

    def test_domain_sale_ok_false(self):
        self._create_product(
            'Product', default_code='SALEOK-FALSE', sale_ok=False)
        content = self._fetch_feed()
        self.assertNotIn(
            'SALEOK-FALSE',
            content,
            'Product with sale_ok=False should NOT appear in feed')

    def test_domain_website_published_false(self):
        self._create_product(
            'Product', default_code='PUB-FALSE', website_published=False)
        content = self._fetch_feed()
        self.assertNotIn(
            'PUB-FALSE',
            content,
            'Product with website_published=False should NOT appear')

    def test_domain_company_id_matches(self):
        self._create_product('Product', default_code='CO-MATCH')
        content = self._fetch_feed()
        self.assertIn(
            'CO-MATCH',
            content,
            'Expected product with matching company_id in feed')

    def test_domain_company_id_false(self):
        self._create_product(
            'Product', default_code='CO-FALSE', company_id=False)
        content = self._fetch_feed()
        self.assertIn(
            'CO-FALSE',
            content,
            'Expected product with company_id=False in feed')

    def test_domain_company_id_other(self):
        self._create_product(
            'Product',
            default_code='CO-OTHER',
            company_id=self.other_company.id)
        content = self._fetch_feed()
        self.assertNotIn(
            'CO-OTHER',
            content,
            'Product with other company_id should NOT appear in feed')

    def test_domain_combined_inclusion(self):
        self._create_product(
            'Valid Default Web', default_code='COMB-VALID-1')
        self._create_product(
            'Valid No Web', default_code='COMB-VALID-2', website_id=False)
        self._create_product(
            'Valid No Co', default_code='COMB-VALID-3', company_id=False)
        content = self._fetch_feed()
        self.assertIn(
            'COMB-VALID-1',
            content,
            'All-matching product should be in feed')
        self.assertIn(
            'COMB-VALID-2',
            content,
            'Product with no website should be in feed')
        self.assertIn(
            'COMB-VALID-3',
            content,
            'Product with no company should be in feed')

    def test_domain_combined_exclusion(self):
        self._create_product('Valid', default_code='COMB-ONLY-VALID')
        self._create_product(
            'No Sale', default_code='COMB-EXCL-SALE', sale_ok=False)
        self._create_product(
            'No Publish', default_code='COMB-EXCL-PUB',
            website_published=False)
        self._create_product(
            'Other Site', default_code='COMB-EXCL-SITE',
            website_id=self.other_website.id)
        self._create_product(
            'Other Co', default_code='COMB-EXCL-CO',
            company_id=self.other_company.id)
        content = self._fetch_feed()
        self.assertIn('COMB-ONLY-VALID', content)
        self.assertNotIn('COMB-EXCL-SALE', content)
        self.assertNotIn('COMB-EXCL-PUB', content)
        self.assertNotIn('COMB-EXCL-SITE', content)
        self.assertNotIn('COMB-EXCL-CO', content)

    def test_xml_structure_has_item_per_product(self):
        self._create_product('Product A', default_code='STRUCT-A')
        self._create_product('Product B', default_code='STRUCT-B')
        content = self._fetch_feed()
        self.assertIn('<g:id>STRUCT-A</g:id>', content)
        self.assertIn('<g:id>STRUCT-B</g:id>', content)
        self.assertIn('<g:title>', content)
        self.assertIn('<g:availability>', content)
        self.assertIn('<g:price>', content)
        self.assertIn('<g:link>', content)
        self.assertIn('<g:image_link>', content)
