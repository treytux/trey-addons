# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    public_name = fields.Char(
        string='Public name',
        required=False,
        translate=True,
        select=True,
        help='Public name for product attributes in website')
