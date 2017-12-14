# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    attribute_ids = fields.Many2many(
        comodel_name='product.attribute',
        relation='public_category_attribute_rel',
        column1='category_id',
        column2='attribute_id',
        string='Attributes')
