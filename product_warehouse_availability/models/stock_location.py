# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    not_availability = fields.Boolean(
        string='Not availability',
        required=False,
        help='If this field is active, no availability will be calculated '
             'for this location.',
    )
