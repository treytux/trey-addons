# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class ProductPack(models.Model):
    _name = 'product.pack'
    _description = 'Product Pack'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        string='Product template')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        domain=[('is_pack', '=', False)])
    quantity = fields.Float(
        string='Quantity',
        default=1.0)
