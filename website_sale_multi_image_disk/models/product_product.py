# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models
from openerp.addons.website.models.website import slugify
from openerp.addons.website_sale_multi_image_disk import (
    multi_image_disk_tools as midt)
import logging
_log = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    name_slug = fields.Char(
        compute='_compute_name_slug',
        string='Slug',
        description='Pattern to retrieve images')

    @api.one
    @api.depends('name')
    def _compute_name_slug(self):
        self.name_slug = self.product_tmpl_id.name
        attributes = [
            attribute_value for attribute_value in self.attribute_value_ids
            if attribute_value.attribute_id.apply_to_images]
        for attribute in attributes:
            self.name_slug += '-%s-%s' % (
                attribute.attribute_id.name,
                attribute.name)
        self.name_slug = slugify(self.name_slug)

    @api.model
    def _get_disk_image(
            self, filename, field='image', max_width=None, max_height=None):
        assert field in ('image', 'image_big', 'image_medium', 'image_small')
        if field != 'image':
            max_width = self.product_tmpl_id.IMAGE_FIELD_SIZES[field][0]
            max_height = self.product_tmpl_id.IMAGE_FIELD_SIZES[field][1]
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
