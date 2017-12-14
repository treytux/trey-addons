# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    supplier_picking_number = fields.Char(
        string='Supplier Picking Number',
        states={'cancel': [('readonly', True)],
                'done': [('readonly', True)]})


class StockMove(models.Model):
    _inherit = 'stock.move'

    gross_measures = fields.Char(
        string='Gross measures')
