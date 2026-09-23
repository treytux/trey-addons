###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase

PIXEL_PNG = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
    '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')


class TestProductIcon(TransactionCase):

    def setUp(self):
        super().setUp()
        self.icon = self.env['product.icon'].create({
            'name': 'Waterproof',
            'image_1920': PIXEL_PNG,
        })
        self.template = self.env['product.template'].create({
            'name': 'Icon Test Product',
        })

    def test_image_mixin_generates_resized_images(self):
        self.assertTrue(self.icon.image_1920)
        self.assertTrue(self.icon.image_128)
        self.assertTrue(self.icon.image_512)

    def test_icon_ids_related_image(self):
        self.template.write({
            'icon_ids': [(0, 0, {'icon_id': self.icon.id, 'sequence': 1})],
        })
        line = self.template.icon_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.icon_id, self.icon)
        self.assertEqual(line.image_128, self.icon.image_128)

    def test_public_user_can_read_icon(self):
        public_user = self.env.ref('base.public_user')
        icon = self.icon.with_user(public_user)
        self.assertEqual(icon.read(['name'])[0]['name'], 'Waterproof')
