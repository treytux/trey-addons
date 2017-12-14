# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def get_price_unit(self, move):
        """ Returns the unit price to store on the quant """
        if move.purchase_line_id:
            price = (
                move.purchase_line_id.price_subtotal /
                move.purchase_line_id.product_qty)
            return price

        return super(StockMove, self).get_price_unit(move)
