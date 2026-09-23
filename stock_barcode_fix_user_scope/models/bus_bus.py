###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class BusBus(models.Model):
    _inherit = 'bus.bus'

    _STOCK_BARCODES_GLOBAL_CHANNELS = (
        'stock_barcodes_scan',
        'stock_barcodes_form_update',
        'stock_barcodes_kanban_update',
    )

    @api.model
    def _sendmany(self, notifications):
        user = self.env.user if self.env.uid else self.env['res.users']
        if user and not user._is_public():
            partner = user.partner_id
            global_channels = self._STOCK_BARCODES_GLOBAL_CHANNELS
            notifications = [
                [
                    partner
                    if isinstance(target, str) and target in global_channels
                    else target,
                    notification_type,
                    message,
                ]
                for target, notification_type, message in notifications
            ]
        return super()._sendmany(notifications)
