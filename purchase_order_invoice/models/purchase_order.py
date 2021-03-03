###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_view_invoice(self):
        if not self._context.get('create_bill', None):
            return super().action_view_invoice()
        wizard = self.env['purchase.order.invoice'].with_context(
            active_id=self.id).create({})
        action = self.env.ref(
            'purchase_order_invoice.purchase_order_invoice_action').read()[0]
        action['res_id'] = wizard.id
        return action
