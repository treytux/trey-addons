# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_product_id = fields.Many2one(
        comodel_name='product.template',
        string='Commission Booking Product',
        help='Product for commission invoicing booking')
