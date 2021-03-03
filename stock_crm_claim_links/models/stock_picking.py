# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    claim_id = fields.Many2one(
        comodel_name='crm.claim',
        string='Claim',
        select=True)
