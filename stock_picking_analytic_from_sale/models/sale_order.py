###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super()._action_confirm()
        for order in self:
            if order.analytic_account_id:
                order._propagate_analytic_to_pickings()
        return res

    def _propagate_analytic_to_pickings(self):
        self.ensure_one()
        if not self.analytic_account_id:
            return
        analytic_account = self.analytic_account_id
        for picking in self.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing'
        ):
            was_done = picking.state == 'done'
            picking.analytic_account_id = analytic_account
            if was_done:
                picking._create_analytic_lines_from_stock_moves()
