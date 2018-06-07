# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    product_default_route = fields.Boolean(
        string='Product default route',
        help='If checked it, when a new product is created, this route will '
        'be marked by default.')
