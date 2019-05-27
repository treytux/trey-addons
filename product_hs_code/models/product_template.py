# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code_id = fields.Many2one(
        comodel_name='product.template.hscode',
        string='HS Code',
        help='Standardized code for international shipping declaration')
