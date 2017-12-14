# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api

param = 'website_sale_shop_by_grid.allow_shopping_with_stock_available'


class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    allow_shopping_with_stock_available = fields.Boolean(
        string='Allow website sales only with stock available')

    @api.multi
    def set_params(self):
        self.ensure_one()
        value = str(self.allow_shopping_with_stock_available)
        self.env['ir.config_parameter'].set_param(param, value)

    @api.model
    def default_get(self, fields):
        res = super(SaleConfigSettings, self).default_get(fields)
        val = self.env['ir.config_parameter'].get_param(param, False)
        res['allow_shopping_with_stock_available'] = (
            val == 'True' and True or False)
        return res
