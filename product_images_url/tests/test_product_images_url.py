###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo.tests import common


class TestProductImagesUrl(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.filename = 'image.png'

    def test_product_images_url(self):
        self.assertFalse(self.product.image)
        self.assertFalse(self.product.product_image_ids)
        self.assertFalse(self.product.product_tmpl_id.image)
        self.assertFalse(self.product.product_tmpl_id.product_image_ids)
        img = open(
            os.path.join(os.path.dirname(__file__), self.filename), 'rb')
        self.product.image = base64.standard_b64encode(img.read())
        self.assertTrue(self.product.image)
        self.assertTrue(self.product.product_tmpl_id.image)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        self.assertEquals(
            '%s/website/image/product.template/%s/image' % (
                base_url, self.product.product_tmpl_id.id),
            self.product.product_tmpl_id.images_url)
        self.assertEquals(
            '%s/website/image/product.product/%s/image' % (
                base_url, self.product.id),
            self.product.images_url)
        self.assertFalse(self.product.product_image_ids)
        self.assertFalse(self.product.product_tmpl_id.product_image_ids)
        self.product.write({
            'product_image_ids': [
                (0, 0, {'image': base64.standard_b64encode(img.read())})
            ],
        })
        self.assertEquals(len(self.product.product_image_ids), 1)
        self.assertEquals(
            len(self.product.product_tmpl_id.product_image_ids), 1)
        self.assertIn(
            '%s/website/image/product.template/%s/image' % (
                base_url, self.product.product_tmpl_id.id),
            self.product.product_tmpl_id.images_url)
        self.assertIn(
            '%s/website/image/product.product/%s/image' % (
                base_url, self.product.id),
            self.product.images_url)
        self.assertIn(
            '%s/website/image/product.image/%s/image' % (
                base_url,
                self.product.product_tmpl_id.product_image_ids[0].id),
            self.product.product_tmpl_id.images_url)
        self.assertIn(
            '%s/website/image/product.image/%s/image' % (
                base_url, self.product.product_image_ids[0].id),
            self.product.images_url)

    def test_product_multiple_variant_attributes(self):
        attr = self.env['product.attribute'].create({
            'name': 'Atribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'type': 'consu',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ]
        })
        self.assertEquals(len(template.product_variant_ids), 3)
        self.assertFalse(template.images_url)
        for variant in template.product_variant_ids:
            self.assertFalse(variant.images_url)
        img = open(
            os.path.join(os.path.dirname(__file__), self.filename), 'rb')
        template.image = base64.standard_b64encode(img.read())
        template.write({
            'product_image_ids': [
                (0, 0, {'image': base64.standard_b64encode(img.read())})
            ],
        })
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        self.assertIn(
            '%s/website/image/product.template/%s/image' % (
                base_url, template.id),
            template.images_url)
        self.assertIn(
            '%s/website/image/product.image/%s/image' % (
                base_url, template.product_image_ids[0].id),
            template.images_url)
        for variant in template.product_variant_ids:
            self.assertIn(
                '%s/website/image/product.product/%s/image' % (
                    base_url, variant.id),
                variant.images_url)
            for image in variant.product_image_ids:
                self.assertIn(
                    '%s/website/image/product.image/%s/image' % (
                        base_url, image.id),
                    variant.images_url)
