# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_product_quantities(self, order):
        products_qty_cart = {}
        for line in order.sudo().order_line:
            products_qty_cart.setdefault(line.product_id.id, 0)
            products_qty_cart[line.product_id.id] += line.product_uom_qty
        return products_qty_cart
