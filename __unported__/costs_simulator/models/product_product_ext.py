# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields

from openerp import models, fields, api


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
     
    amortization_rate = fields.Float(
        string='Amortization Rate',
        digits=(3, 2))
    indirect_cost_rate = fields.Float(
        string='Indirect Cost Rate',
        digits=(3, 2))
