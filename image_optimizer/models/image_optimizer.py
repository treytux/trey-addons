###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io

from odoo import models
from PIL import Image


class ImageOptimizer(models.Model):
    _name = 'image.optimizer'

    def _get_aspect_ratio(self, width, height):
        return width / height

    def attachment_save_image(self, optimized_image_data):
        self.datas = optimized_image_data

    def all_save_image(self, optimized_image_data):
        self.image = optimized_image_data

    def image_resize(self, image, size, aspect_ratio):
        image = image.resize((size, int(round(size / aspect_ratio))))
        return image

    def optimize_image(self, image):
        quality = 90
        name = self._name
        while quality >= 30:
            optimized_image = image
            optimized_image_buffer = io.BytesIO()
            optimized_image.save(
                optimized_image_buffer, format='JPEG', quality=quality)
            optimized_image_size = optimized_image_buffer.tell()
            if optimized_image_size <= (1024 * 1024) and quality >= 30:
                optimized_image_buffer.seek(0)
                optimized_image_data = optimized_image_buffer.read()
                optimized_image_data = base64.b64encode(optimized_image_data)
                if name == 'ir.attachment':
                    self.attachment_save_image(optimized_image_data)
                    return True
                else:
                    self.all_save_image(optimized_image_data)
                    return True
            else:
                quality -= 3
        return False

    def optimize_images(self, datas):
        image_data = io.BytesIO(base64.b64decode(datas))
        image = Image.open(image_data)
        if len(image_data.getbuffer()) <= (1024 * 1024):
            return True
        original_width, original_height = image.size
        aspect_ratio = self._get_aspect_ratio(original_width, original_height)
        if original_width > 7680:
            image = self.image_resize(image, 7680, aspect_ratio)
            if self.optimize_image(image):
                return True
        if original_width > 3840:
            image = self.image_resize(image, 3840, aspect_ratio)
            if self.optimize_image(image):
                return True
        if original_width > 2048:
            image = self.image_resize(image, 2048, aspect_ratio)
            if self.optimize_image(image):
                return True
        if original_width > 1980:
            image = self.image_resize(image, 1980, aspect_ratio)
            if self.optimize_image(image):
                return True
        image = self.image_resize(image, 1024, aspect_ratio)
        if self.optimize_image(image):
            return True
