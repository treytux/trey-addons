# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    is_sale_one_purchase = fields.Boolean(
        string='One Sale One Purchase',
    )
    is_drop_shipping = fields.Boolean(
        string='DropShipping',
    )
