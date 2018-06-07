# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sold_ids = fields.One2many(
        comodel_name='product.sold',
        inverse_name='partner_id',
        string='Products Sold')
