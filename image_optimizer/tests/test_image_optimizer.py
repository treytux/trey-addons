###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import os

from odoo.tests.common import TransactionCase
from PIL import Image


class TestsImageOptimizer(TransactionCase):

    def setUp(self):
        super().setUp()
        relative_rute_1 = 'img/image.jpg'
        relative_rute_2 = 'img/image_2.jpg'
        cwd = os.path.dirname(os.path.abspath(__file__))
        absolute_rute_1 = os.path.join(cwd, relative_rute_1)
        absolute_rute_2 = os.path.join(cwd, relative_rute_2)
        with open(absolute_rute_1, 'rb') as f:
            self.image_data_1 = io.BytesIO(f.read())
        self.image_1 = Image.open(absolute_rute_1)
        self.image_size_1 = len(self.image_data_1.getvalue())
        with open(absolute_rute_2, 'rb') as f:
            self.image_data_2 = io.BytesIO(f.read())
        self.image_2 = Image.open(absolute_rute_2)
        self.image_size_2 = len(self.image_data_2.getvalue())

    def test_image_optimizer_attactchment(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'image',
            'type': 'binary',
            'mimetype': 'image/jpeg',
            'datas': base64.b64encode(self.image_data_1.getvalue())
        })
        self.assertGreater(self.image_size_1, attachment.file_size)
        self.assertLess(attachment.file_size, (1024 * 1024))
        original_width, original_height = self.image_1.size
        aspect_ratio_original = round((original_width / original_height), 2)
        new_datas = io.BytesIO(base64.b64decode(attachment.datas))
        new_image = Image.open(new_datas)
        new_width, new_height = new_image.size
        aspect_ratio_new = round((new_width / new_height), 2)
        self.assertEqual(aspect_ratio_original, aspect_ratio_new)
        attachment.write({
            'datas': base64.b64encode(self.image_data_2.getvalue())
        })
        self.assertGreater(self.image_size_2, attachment.file_size)
        self.assertLess(attachment.file_size, (1024 * 1024))
        original_width, original_height = self.image_2.size
        aspect_ratio_original = round((original_width / original_height), 2)
        new_datas = io.BytesIO(base64.b64decode(attachment.datas))
        new_image = Image.open(new_datas)
        new_width, new_height = new_image.size
        aspect_ratio_new = round((new_width / new_height), 2)
        self.assertEqual(aspect_ratio_original, aspect_ratio_new)

    def test_image_optimizer_user(self):
        user = self.env['res.users'].create({
            'name': 'test',
            'login': 'test',
            'image': base64.b64encode(self.image_data_1.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(user.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_1, image_size)
        self.assertLess(image_size, (1024 * 1024))
        user.write({
            'image': base64.b64encode(self.image_data_2.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(user.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_2, image_size)
        self.assertLess(image_size, (1024 * 1024))

    def test_image_optimizer_partner(self):
        partner = self.env['res.partner'].create({
            'name': 'test',
            'image': base64.b64encode(self.image_data_1.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(partner.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_1, image_size)
        self.assertLess(image_size, (1024 * 1024))
        partner.write({
            'image': base64.b64encode(self.image_data_2.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(partner.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_2, image_size)
        self.assertLess(image_size, (1024 * 1024))

    def test_image_optimizer_product(self):
        product = self.env['res.partner'].create({
            'name': 'test',
            'image': base64.b64encode(self.image_data_1.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(product.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_1, image_size)
        self.assertLess(image_size, (1024 * 1024))
        product.write({
            'image': base64.b64encode(self.image_data_2.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(product.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_2, image_size)
        self.assertLess(image_size, (1024 * 1024))

    def test_image_optimizer_template(self):
        template = self.env['res.partner'].create({
            'name': 'test',
            'image': base64.b64encode(self.image_data_1.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(template.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_1, image_size)
        self.assertLess(image_size, (1024 * 1024))
        template.write({
            'image': base64.b64encode(self.image_data_2.getvalue())
        })
        image_datas = io.BytesIO(base64.b64decode(template.image))
        image_size = len(image_datas.getbuffer())
        self.assertGreater(self.image_size_2, image_size)
        self.assertLess(image_size, (1024 * 1024))
