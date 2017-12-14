# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    apply_discount_group = fields.Boolean(
        default=True,
        string='Apply Discount Group')
