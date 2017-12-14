# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import fields, models
from openerp.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.template'

    list_price = fields.Float(
        string='Sale Price',
        digits=dp.get_precision('Product Price'),
        groups="base.group_user", company_dependent=True)
