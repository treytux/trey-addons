# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields
import logging
_log = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    reverse_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Reverse picking',
        help="Hidden field to relate with the reverse stock picking.")
