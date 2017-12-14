# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields
from .gallery_image import update_sequences_gallery

import logging

_log = logging.getLogger(__name__)


class GalleryImageTemplate(models.Model):
    _inherit = "gallery_image"
    _name = "product_template.gallery_image"
    _description = "Gallery Image for product.template"

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string=u'Product Template'
    )
    attribute_value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        relation='product_template_gallery_image_product_attribute_value_rel',
        column1='image_id',
        column2='att_id'
    )
    alternative_text = fields.Char(
        string=u'Alternative Text',
        store=True,
        translate=True
    )

    @property
    def object_relation_name(self):
        return "product_tmpl_id"

    def _compute_name_image(self, name=None, sequence=None):
        """
        Devuelve el nombre de la imagen en función del nombre del objecto
        y su sequencia
        """
        template = self.product_tmpl_id
        name = template.name
        if 'public_name' in template:
            name = template.public_name
        return super(GalleryImageTemplate, self)._compute_name_image(name=name)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gallery_ids = fields.One2many(
        comodel_name='product_template.gallery_image',
        inverse_name='product_tmpl_id'
    )

    def write(self, cr, uid, ids, vals, context=None):
        r = super(ProductTemplate, self).write(cr, uid, ids, vals, context)
        update_sequences_gallery(self, cr, uid, ids, 'gallery_ids',
                                 'product_template.gallery_image')
        return r
