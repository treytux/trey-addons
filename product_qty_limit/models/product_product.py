# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_limit = fields.Integer(
        string='Qty Limit',
        help='Maximum quantity allowed in sales. 0 means no limit.')
