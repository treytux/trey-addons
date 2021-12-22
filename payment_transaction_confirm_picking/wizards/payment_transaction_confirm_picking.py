###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class PaymentTransactionConfirmPicking(models.TransientModel):
    _name = 'payment.transaction.confirm.picking'
    _description = 'Payment transaction confirm picking'

    @api.multi
    def action_wizard_confirm_transaction_and_picking(self):
        active_ids = self.env.context['active_ids']
        transactions = self.env['payment.transaction'].browse(
            active_ids).filtered(lambda t: t.state == 'pending')
        if not transactions:
            raise exceptions.Warning(_('No transactions to confirm'))
        transactions.action_confirm_transaction_and_picking()
        return {'type': 'ir.actions.act_window_close'}
