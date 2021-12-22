###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
# NOTE: For test product_image_ids or if you has installed website_sale addon
# you must add website_sale addon to depends in __manifest__
import os
import shutil

from odoo.tests.common import TransactionCase
from odoo.tools import config


class TestProductImagesImportFromFolder(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'type' in self.env['product.attribute']._fields:
            attr = self.env['product.attribute'].create({
                'name': 'Attribute test',
                'type': 'select',
            })
        else:
            attr = self.env['product.attribute'].create({
                'name': 'Attribute test',
            })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        self.template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ]
        })
        self.folder = os.path.join(
            config.filestore(self.env.cr.dbname), 'images2import')
        os.makedirs(self.folder, exist_ok=True)
        self._remove_files()

    def tearDown(self):
        self._remove_files()

    def _remove_files(self):
        files = [
            os.path.join(self.folder, f)
            for f in os.listdir(self.folder)
            if os.path.isfile(os.path.join(self.folder, f))]
        for file in files:
            os.remove(file)

    def _create_image(self, fname):
        fname_dst = os.path.join(self.folder, '%s.png' % fname)
        shutil.copy(
            os.path.join(os.path.dirname(__file__), 'sample.png'),
            fname_dst)
        return fname_dst

    def test_importimages(self):
        image_fname = self._create_image(self.template.id)
        self._create_image('0000')
        self.assertFalse(self.template.image)
        self.assertFalse(self.template.product_variant_id.image)
        self.assertTrue(os.path.exists(image_fname))
        self.template.cron_product_template_import_images_from_folder()
        self.assertTrue(self.template.image)
        self.assertTrue(self.template.product_variant_id.image)
        self.assertFalse(os.path.exists(image_fname))

    def test_import_variant_images(self):
        self._create_image(self.template.id)
        self._create_image('%s-1' % self.template.id)
        self._create_image('%s-2' % self.template.id)
        self.assertFalse(self.template.image)
        self.template.cron_product_template_import_images_from_folder()
        self.assertTrue(self.template.image)
        self.assertTrue(self.template.product_variant_id.image)
        if 'product_image_ids' not in self.template._fields:
            return
        self.assertTrue(self.template.product_image_ids)
        self.assertTrue(self.template.product_image_ids[0].image)
