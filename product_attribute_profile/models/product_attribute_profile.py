# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductAttributeProfile(models.Model):
    _name = 'product.attribute.profile'
    _description = 'Product Attribute Profile'

    name = fields.Char(
        string='Profile',
        required=True)
    attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute',
        required=True)
    line_ids = fields.One2many(
        comodel_name='product.attribute.profile.line',
        inverse_name='profile_id',
        string='Lines')
