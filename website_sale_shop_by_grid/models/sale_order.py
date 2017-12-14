# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_order_product_qtys(self, order):
        products_qty_cart = {}
        for line in order.sudo().order_line:
            pp = line.product_id
            if pp.id not in products_qty_cart:
                products_qty_cart.update({pp.id: line.product_uom_qty})
            else:
                products_qty_cart[pp.id] += pp.product_uom_qty
        return products_qty_cart
