# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    active = fields.Boolean(
        string='Active',
        default=True,
        help='If the active field is set to False, it will allow you to hide '
             'the warehouse without removing it.')
