###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import api, fields, models
from openerp.addons.website.models.website import slugify
import base64


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_image_ids = fields.One2many(
        comodel_name='product.image.transient',
        compute='_compute_images',
        store=False,
        inverse_name=None,
        string='Images')
    image = fields.Binary(
        compute='_compute_images',
        store=False)
    image_medium = fields.Binary(
        compute='_compute_images',
        store=False)
    image_small = fields.Binary(
        compute='_compute_images',
        store=False)
    name_slug = fields.Char(
        compute='_compute_name_slug',
        string='Slug',
        description='Pattern to retrieve images')

    @api.one
    @api.depends('name')
    def _compute_name_slug(self):
        website = self.env['website'].default_website_get()
        name = self.name
        if not website.image_slug_translate:
            name = self.with_context(lang=website.default_lang_code).name
        self.name_slug = slugify(name)

    @api.one
    @api.depends('name_slug')
    def _compute_images(self):
        self.product_image_ids = False
        if not self.name_slug:
            return
        website = self.env['website'].default_website_get()
        images = {
            'image': (1024, 1024),
            'image_medium': (128, 128),
            'image_small': (64, 64)}
        for k, size in images.items():
            img, mime = website.image_get(self.name_slug, size=size)
            self[k] = img and base64.b64encode(img) or False
        images = []
        for i, file in enumerate(website.image_files_get(self.name_slug)):
            if i == 0:
                continue
            img, mime = website.image_get(file, size=[64, 64])
            image = self.env['product.image.transient'].create({
                'name': file,
                'product_tmpl_id': self.id,
                'image': img and base64.b64encode(img) or False})
            images.append(image)
        self.product_image_ids = [i.id for i in images]

    @api.multi
    def image_files_get(self, website=None):
        self.ensure_one()
        website = self.env['website'].default_website_get()
        return website.image_files_get(self.name_slug)
