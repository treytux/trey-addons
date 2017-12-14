# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    recommended_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Recommended pricelist')
