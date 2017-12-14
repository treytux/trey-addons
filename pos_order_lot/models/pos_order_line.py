# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial Number')
