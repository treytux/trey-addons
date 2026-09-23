###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _action_launch_stock_rule(self):
        if self.env.context.get('skip_stock_picking_on_confirmation'):
            return True
        return super()._action_launch_stock_rule()
