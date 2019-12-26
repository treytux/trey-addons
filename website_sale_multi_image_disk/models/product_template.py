# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import json
from openerp import api, fields, models
from openerp.addons.website.models.website import slugify
from openerp.addons.website_sale_multi_image_disk import (
    multi_image_disk_tools as midt)
import logging
_log = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    IMAGE_FIELD_SIZES = {
        'image_big': (1024, 1024),
        'image_medium': (300, 300),
        'image_small': (64, 64)
    }

    name_slug = fields.Char(
        compute='_compute_name_slug',
        string='Slug',
        description='Pattern to retrieve images')

    @api.one
    @api.depends('name')
    def _compute_name_slug(self):
        self.name_slug = slugify(self.name)

    @api.model
    def get_variant_slugs(self):
        return sorted(list(set([
            variant.name_slug for variant in self.product_variant_ids])))

    @api.model
    def _get_disk_image(
            self, filename, field='image', max_width=None, max_height=None):
        assert field in ('image', 'image_big', 'image_medium', 'image_small')
        if field != 'image':
            max_width = self.IMAGE_FIELD_SIZES[field][0]
            max_height = self.IMAGE_FIELD_SIZES[field][1]
        return midt.get_disk_image(
            filename, max_width=max_width, max_height=max_height)

    @api.model
    def _get_default_disk_image(
            self, field='image', max_width=None, max_height=None):
        images = midt.get_disk_images(self.name_slug)
        if images:
            return self._get_disk_image(
                images[0], field=field, max_width=max_width,
                max_height=max_height)
        _log.warning(('Missing image for %s %s %s' % (
            self._name, self.id, self.name_slug)))
        return None

    @api.model
    def _get_variants_gallery(self, lang=None):
        gallery = {}
        translate = self.env['ir.config_parameter'].get_param(
            'website_sale_multi_image_disk.translate') == 'True'
        variants = (
            (lang and not translate) and self.with_context(
                lang=lang).product_variant_ids or self.product_variant_ids)
        for v in variants:
            gallery.update({v.id: midt.get_disk_images(v.name_slug)})
        return json.dumps(gallery)
