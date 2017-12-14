# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    supplier_ref = fields.Char(
        string='Supplier Ref.')
