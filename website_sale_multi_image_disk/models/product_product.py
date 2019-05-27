###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import api, fields, models
from openerp.addons.website.models.website import slugify
import base64


class ProductProduct(models.Model):
    _inherit = 'product.product'

    name_slug = fields.Char(
        compute='_compute_name_slug',
        string='Slug',
        description='Pattern to retrieve images')
    image_variant = fields.Binary(
        compute='_compute_product_images')
    product_image_ids = fields.One2many(
        comodel_name='product.image.transient',
        compute='_compute_product_images',
        store=False,
        inverse_name=None,
        string='Images')

    @api.one
    @api.depends('name')
    def _compute_name_slug(self):
        website = self.env['website'].default_website_get()
        this = self.with_context(lang=website.default_lang_code)
        parts = [this.product_tmpl_id.name or '']
        parts += [
            '%s-%s' % (attr.attribute_id.name, attr.name)
            for attr in this.attribute_value_ids
            if attr.attribute_id.apply_to_images]
        self.name_slug = slugify('-'.join([str(p) for p in parts if p]))

    @api.one
    @api.depends('name_slug')
    def _compute_product_images(self):
        if self.name_slug == self.product_tmpl_id.name_slug:
            self.image_variant = False
            self.product_image_ids = self.product_tmpl_id.product_image_ids
            return
        self.product_image_ids = False
        if not self.name_slug:
            return
        website = self.env['website'].default_website_get()
        images = []
        for i, file in enumerate(website.image_files_get(self.name_slug)):
            img, mime = website.image_get(file)
            if i == 0:
                self.image_variant = img and base64.b64encode(img) or False
                continue
            image = self.env['product.image.transient'].create({
                'name': file,
                'product_tmpl_id': self.product_tmpl_id.id,
                'image': img and base64.b64encode(img) or False})
            images.append(image)
        self.product_image_ids = [i.id for i in images]
