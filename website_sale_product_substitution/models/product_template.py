# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    substitution_product = fields.Many2one(
        comodel_name='product.template',
        string='Substitution Product',
    )
