###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    images_url = fields.Char(
        string='Images URL',
        compute='_compute_images_variant_url',
    )

    @api.depends('image', 'product_image_ids')
    def _compute_images_variant_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        for product in self:
            images = []
            if product.image:
                images.append('%s/website/image/product.product/%s/image' % (
                    base_url, product.id))
            for image in product.product_image_ids:
                images.append('%s/website/image/product.image/%s/image' % (
                    base_url, image.id))
            product.images_url = ', '.join(images)
