# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockQuantModifyPriceUnit(models.TransientModel):
    _name = 'stock.quant.modify.price.unit'

    cost_modified = fields.Float(
        string='Cost')

    @api.one
    def button_accept(self):
        quant = self.env['stock.quant'].browse(self.env.context['active_id'])
        quant.cost = self.cost_modified
