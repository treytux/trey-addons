# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    subscription = fields.Boolean(
        string='Subscription')
