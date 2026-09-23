###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _confirm_custom_orders(self):
        for tx in self:
            if len(tx.sale_order_ids) != 1:
                continue
            quotation = tx.sale_order_ids.filtered(
                lambda so: so.state in ('draft', 'sent'))
            if not quotation:
                continue
            quotation.with_context(send_email=True).action_confirm()

    def _process_notification_data(self, notification_data):
        if (self.provider_code == 'custom'
                and self.provider_id.confirm_orders_automatically):
            self._confirm_custom_orders()
        return super()._process_notification_data(notification_data)
