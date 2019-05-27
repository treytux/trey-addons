# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    auto_return_picking = fields.Boolean(
        string='Create automatic return picking')
