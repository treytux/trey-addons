# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    agent = fields.Boolean(
        string='For agents only')
