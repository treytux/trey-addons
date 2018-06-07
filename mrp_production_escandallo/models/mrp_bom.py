# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    mrp_production_ids = fields.One2many(
        comodel_name='mrp.production',
        inverse_name='bom_id',
        string='Production Order')
