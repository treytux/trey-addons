# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    sold_id = fields.Many2one(
        comodel_name='product.sold',
        string='Product Sold')
