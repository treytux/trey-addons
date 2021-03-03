###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _website_product_id_change(self, order_id, product_id, qty=0):
        res = super()._website_product_id_change(order_id, product_id, qty)
        order_line = self._cart_find_product_line(product_id)[:1]
        if not order_line or not order_line.product_id.pack_ok:
            return res
        if (
                order_line.pack_parent_line_id
                and order_line.pack_parent_line_id.pack_component_price in
                ['ignored', 'totalized']
        ):
            res['price_unit'] = 0
        if order_line.pack_child_line_ids:
            if order_line.pack_component_price == 'detailed':
                res['price_unit'] = 0
        return res

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0,
                     **kwargs):
        self.ensure_one()
        order_line = self._cart_find_product_line(product_id, line_id)[:1]
        context = self.env.context.copy()
        if (
                order_line
                and order_line.pack_parent_line_id
                and order_line.pack_parent_line_id.pack_component_price in
                ['ignored', 'totalized']
        ):
            context['fixed_price'] = True
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product.pack_ok and product.pack_component_price == 'detailed':
                context['fixed_price'] = True
        self.env.context = context
        return super()._cart_update(
            product_id, line_id, add_qty, set_qty, **kwargs)
