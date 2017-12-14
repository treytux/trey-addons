# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    profile_ids = fields.One2many(
        comodel_name='product.attribute.profile',
        inverse_name='attribute_id',
        string='Profile')
