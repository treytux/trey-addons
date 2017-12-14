# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class InventoryFake(object):
    def __init__(self, inventory, product=None, lot=None):
        self.id = inventory.id
        self.location_id = inventory.location_id
        self.product_id = product
        self.lot_id = lot
        self.package_id = inventory.package_id
        self.filter = 'season_ids'
        self.partner_id = inventory.partner_id


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.model
    def _get_available_filters(self):
        res_filters = super(StockInventory, self)._get_available_filters()
        res_filters.append(('season_ids', _('Products Season')))
        return res_filters

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season')
    season_ids = fields.Many2many(
        comodel_name='product.season',
        relation='rel_product_season',
        column1='season_id',
        column2='product_id',
        string='Season')
    filter = fields.Selection(
        selection=_get_available_filters,
        string='Selection Filter',
        required=True)

    @api.model
    def _get_inventory_lines(self, inventory):
        if inventory.filter != 'season_ids':
            return super(StockInventory, self)._get_inventory_lines(inventory)
        vals = []
        product_tmpls = self.env['product.template'].search(
            [('season_id', 'in', inventory.season_ids.ids)])
        products = self.env['product.product'].search(
            [('product_tmpl_id', 'in', product_tmpls.ids)])
        for product in products:
            fake_inventory = InventoryFake(inventory, product=product)
            vals += super(StockInventory, self)._get_inventory_lines(
                fake_inventory)
        return vals
