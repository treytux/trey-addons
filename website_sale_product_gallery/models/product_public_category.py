# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields
from .gallery_image import update_sequences_gallery

import logging
_log = logging.getLogger(__name__)


class GalleryImageProductPublicCategory(models.Model):
    _inherit = "gallery_image"
    _name = "product_public_category.gallery_image"
    _description = "Gallery Image for product.public.category"

    category_id = fields.Many2one(
        comodel_name='product.public.category',
        string=u'Public Category'
    )

    @property
    def object_relation_name(self):
        return "category_id"


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    gallery_ids = fields.One2many(
        comodel_name='product_public_category.gallery_image',
        inverse_name='category_id'
    )

    def write(self, cr, uid, ids, vals, context=None):
        r = super(ProductPublicCategory, self).write(cr, uid, ids, vals,
                                                     context)
        update_sequences_gallery(self, cr, uid, ids, 'gallery_ids',
                                 'product_public_category.gallery_image')
        return r
