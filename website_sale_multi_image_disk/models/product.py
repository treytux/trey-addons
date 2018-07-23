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

IMAGE_FIELD_SIZES = {
    'image_big': (1024, 1024), 'image_medium': (300, 300),
    'image_small': (64, 64)}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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
        # TODO: Si se comprueba antes este assert desde la llamada no es
        # necesario hacerlo aquí también
        assert field in ('image', 'image_big', 'image_medium', 'image_small')
        if field != 'image':
            max_width = IMAGE_FIELD_SIZES[field][0]
            max_height = IMAGE_FIELD_SIZES[field][1]
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


class Product(models.Model):
    _inherit = 'product.product'

    name_slug = fields.Char(
        compute='_compute_name_slug',
        string='Slug',
        description='Pattern to retrieve images')

    @api.one
    @api.depends('name')
    def _compute_name_slug(self):
        # TODO: Incluir dependencia módulo ordenación attributos para
        # poder controlar los slugs de las variantes si hay más de un
        # atributo que afecta a la imagen
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
        # TODO: Si se comprueba antes este assert desde la llamada no es
        # necesario hacerlo aquí también
        assert field in ('image', 'image_big', 'image_medium', 'image_small')
        if field != 'image':
            max_width = IMAGE_FIELD_SIZES[field][0]
            max_height = IMAGE_FIELD_SIZES[field][1]
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


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    apply_to_images = fields.Boolean(
        string='Apply to images',
        description='Product disk images will include this attribute')
