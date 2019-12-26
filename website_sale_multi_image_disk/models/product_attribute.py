# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    apply_to_images = fields.Boolean(
        string='Apply to images',
        description='Product disk images will include this attribute')
