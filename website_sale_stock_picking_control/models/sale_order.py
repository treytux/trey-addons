###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _skip_stock_picking_on_confirmation(self):
        self.ensure_one()
        return bool(self.website_id.sale_order_skip_stock_picking)

    @api.multi
    def _action_confirm(self):
        orders_skip_picking = self.filtered(
            lambda order: order._skip_stock_picking_on_confirmation())
        orders_pickings = self - orders_skip_picking
        if orders_pickings:
            res = super(SaleOrder, orders_pickings)._action_confirm()
        if orders_skip_picking:
            res = super(SaleOrder, orders_skip_picking.with_context(
                skip_stock_picking_on_confirmation=True)
            )._action_confirm()
        return res
