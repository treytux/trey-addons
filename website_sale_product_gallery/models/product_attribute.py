# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import fields, api
from openerp.osv import osv


class ProductAttribute(osv.osv):
    _inherit = "product.attribute"

    affects_image = fields.Boolean(
        string=u"Active gallery?",
        help='This attribute active image gallery?'
    )


class ProductAttributeValue(osv.osv):
    _inherit = "product.attribute.value"
    order = 'sequence'

    affects_image = fields.Boolean(
        compute='_compute_affects_image',
        store=True,
        help='This attribute value active image gallery?'
    )

    @api.one
    @api.depends('attribute_id', 'attribute_id.affects_image')
    def _compute_affects_image(self):
        self.affects_image = self.attribute_id.affects_image
