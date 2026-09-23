###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderConfirmAndPay(models.TransientModel):
    _inherit = 'sale.order.confirm_and_pay'

    def call_signature_picking_portal(self, context):
        module_name = 'portal_stock_picking_signature'
        action_name = 'signature_picking_sale_session_action'
        action = self.env.ref('%s.%s' % (module_name, action_name))
        self.sale_id.picking_ids[0].pending_signed = 'pending'
        context['picking'] = self.sale_id.picking_ids[0].id
        vals = action.read()[0]
        vals['context'] = context
        return vals

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def action_credit(self):
        context = self.env.context.copy()
        context['avoid_print_report_picking'] = True
        self.env.context = context
        return super().action_credit()

    def action_print_picking(self):
        if self.env.context.get('avoid_print_report_picking'):
            return self._reopen_view()
        return super().action_print_picking()
