###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PurchaseOrderCheck(models.TransientModel):
    _name = 'purchase.order.check'
    _description = 'Purchase Order Check'

    @api.multi
    def action_check_status(self):
        active_ids = self.env.context['active_ids']
        purchases = self.env['purchase.order'].browse(active_ids)
        if not purchases:
            return
        self.env['purchase.order'].ede_check_status(purchases)
