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
        self.filter = 'product_categories'
        self.partner_id = inventory.partner_id


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.model
    def _get_available_filters(self):
        res_filters = super(StockInventory, self)._get_available_filters()
        res_filters.append(('product_categories', _('Product categories')))
        return res_filters

    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product category')
    product_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='inventory_category_rel',
        column1='inventory_id',
        column2='product_category_id',
        string='Product categories')
    filter = fields.Selection(
        selection=_get_available_filters)

    @api.model
    def _get_inventory_lines(self, inventory):
        if inventory.filter != 'product_categories':
            return super(StockInventory, self)._get_inventory_lines(inventory)
        vals = []
        products = self.env['product.product'].search(
            [('categ_id', 'in', inventory.product_category_ids.ids)])
        for product in products:
            fake_inventory = InventoryFake(inventory, product=product)
            vals += super(StockInventory, self)._get_inventory_lines(
                fake_inventory)
        return vals
