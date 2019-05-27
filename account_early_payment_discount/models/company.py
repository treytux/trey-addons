# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    discount_product_id = fields.Many2one(
        comodel_name='product.product',
        string="Early Payment Discount Product",
        required=False,
        domain=[('type', '=', 'service')])
