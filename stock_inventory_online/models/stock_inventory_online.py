# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockInventoryOnline(models.Model):
    _name = 'stock.inventory.online'

    name = fields.Char(
        string='Name',
        required=True)
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='rel_stock_inventory_online_user',
        column1='stock_inventory_online_id',
        column2='user_id')
    season_ids = fields.Many2many(
        comodel_name='product.season',
        relation='rel_stock_inventory_online_season',
        column1='stock_inventory_online_id',
        column2='season_id')
