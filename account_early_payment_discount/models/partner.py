# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    early_discount = fields.Float(
        string='% Early Payment Discount',
        help='Early Payment Discount in %.')
