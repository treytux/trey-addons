# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    apply_sale_discount = fields.Boolean(
        string='Apply sale discount',
        default=True,
        help="If marked, the variants of this product template will be "
             "consider for the sales discount calculation.")
