# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    qty_available = fields.Float(
        related="product_id.qty_available",
        string='Quantity On Hand',
        readonly=True)
    virtual_available = fields.Float(
        related="product_id.virtual_available",
        string='Forecast Quantity',
        readonly=True)
