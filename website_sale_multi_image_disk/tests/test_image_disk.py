###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase
import os

COMMIT_CHANGES = False


class TestImageDisk(HttpCase):

    def get_sample(self, fname=''):
        return os.path.join(os.path.dirname(__file__), 'sample', fname)

    def get_samples(self, extension='.jpg'):
        return [
            f for f in os.listdir(self.get_sample()) if f.endswith(extension)]

    def setUp(self):
        super(TestImageDisk, self).setUp()
        self.website = self.env['website'].search([], limit=1)
        self.website.image_slug_path = self.get_sample()

    def tearDown(self):
        super(TestImageDisk, self).tearDown()
        if COMMIT_CHANGES:
            self.env.cr.commit()

    def test_product_images_ids(self):
        tmpl = self.env.ref('product.product_product_4_product_template')
        self.assertEqual(len(tmpl.product_image_ids.ids), 4)

    def test_check_samples(self):
        path = self.get_sample()
        self.assertTrue(os.path.exists(path))
        jpg_files = self.get_samples('.jpg')
        self.assertGreaterEqual(len(jpg_files), 2)
        jpge_files = self.get_samples('.jpeg')
        self.assertGreaterEqual(len(jpge_files), 2)

    def test_slug_lang(self):
        lang_es = self.env.ref('base.lang_es')
        lang_en = self.env.ref('base.lang_en')
        self.website.image_slug_translate = False
        self.website.default_lang_id = lang_en.id
        tmpl = self.env.ref('product.product_product_4_product_template')
        self.assertEqual(tmpl.name_slug, 'ipad-retina-display')
        self.website.default_lang_id = lang_es.id
        tmpl.name = tmpl.name
        self.assertEqual(tmpl.name_slug, 'ipad-con-pantalla-retina')

    def test_slug_files(self):
        tmpl = self.env.ref('product.product_product_4_product_template')
        files = tmpl.image_files_get()
        self.assertEqual(len(files), 4)
        for file in files:
            self.assertTrue(os.path.exists(self.website.image_path(file)))

    def test_load_image_from_website(self):
        tmpl = self.env.ref('product.product_product_4_product_template')
        r = self.url_open(
            '/web/image/product.template/%s/image' % tmpl.id, timeout=90)
        self.assertEqual(r.status_code, 200)
        r = self.url_open(
            '/web/image/product.template/%s/image/30x30' % tmpl.id, timeout=90)
        self.assertEqual(r.status_code, 200)
