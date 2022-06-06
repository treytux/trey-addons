###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    images_url = fields.Char(
        string='Images URL',
        compute='_compute_images_url',
    )

    @api.depends('image', 'product_image_ids')
    def _compute_images_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        for product_tmpl in self:
            images = []
            if product_tmpl.image:
                images.append('%s/website/image/product.template/%s/image' % (
                    base_url, product_tmpl.id))
            for image in product_tmpl.product_image_ids:
                images.append('%s/website/image/product.image/%s/image' % (
                    base_url, image.id))
            product_tmpl.images_url = ', '.join(images)
