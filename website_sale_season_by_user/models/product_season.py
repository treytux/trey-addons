# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductSeason(models.Model):
    _inherit = 'product.season'

    agent = fields.Boolean(
        string='For agents only')
    public = fields.Boolean(
        string='Public')
