###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            transactions = order.transaction_ids.filtered(
                lambda t: t.state == 'pending')
            pickings = order.picking_ids.filtered(
                lambda p: p.state in ('waiting', 'confirmed', 'assigned'))
            if not transactions or not pickings:
                continue
            status = self.env.user.company_id.manual_payment_picking_state
            for picking in pickings:
                if status == 'draft':
                    picking.action_cancel()
                    for move in picking.move_lines:
                        move.state = 'draft'
                picking.action_toggle_is_locked()
        return res
