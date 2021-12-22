###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.multi
    def action_confirm_transaction_and_picking(self):
        for transaction in self:
            if transaction.state != 'pending':
                continue
            for sale in transaction.sale_order_ids:
                picking_status = \
                    self.env.user.company_id.manual_payment_picking_state
                payment_status = self.env.user.company_id.manual_payment_state
                if picking_status == 'draft':
                    pickings = sale.picking_ids.filtered(
                        lambda p: p.state == 'draft')
                    if not pickings:
                        continue
                    for picking in pickings:
                        picking.action_confirm()
                pickings = sale.picking_ids.filtered(
                    lambda p: p.is_locked is False)
                if not pickings:
                    continue
                for picking in pickings:
                    picking.action_toggle_is_locked()
                transaction.state = payment_status
        return True
