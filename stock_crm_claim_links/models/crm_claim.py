# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='claim_id',
        string='Stock Pickings')
