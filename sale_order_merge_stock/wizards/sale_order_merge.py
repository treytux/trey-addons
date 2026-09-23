###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class SaleOrderMerge(models.TransientModel):
    _inherit = 'sale.order.merge'

    def action_merge(self):
        orders = self.env['sale.order'].browse(self._context['active_ids'])
        warehouse = orders[0].warehouse_id
        warehouse_orders = orders.filtered(
            lambda o: o.warehouse_id == warehouse)
        if len(orders) != len(warehouse_orders):
            raise exceptions.UserError(
                _('You can only merge orders from the same warehouse'))
        return super().action_merge()
