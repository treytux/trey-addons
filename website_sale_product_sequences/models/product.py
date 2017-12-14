# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class Product(models.Model):
    _inherit = 'product.product'
    _order = 'website_sequence_product'

    website_sequence_product = fields.Integer(
        string='Product sequence')
