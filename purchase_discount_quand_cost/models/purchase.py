# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _prepare_order_line_move(self, order, order_line, picking_id,
                                 group_id):
        res = super(PurchaseOrder, self)._prepare_order_line_move(
            order=order, order_line=order_line, picking_id=picking_id,
            group_id=group_id)
        new_price = (order_line.price_subtotal / order_line.product_qty)
        res[0]['price_unit'] = new_price
        return res
