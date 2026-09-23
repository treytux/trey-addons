###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderConfirmAndPay(models.TransientModel):
    _inherit = 'sale.order.confirm_and_pay'

    def call_signature_picking_portal(self):
        module_name = 'portal_stock_picking_signature'
        action_name = 'signature_picking_sale_session_action'
        vals = self.env['ir.actions.actions']._for_xml_id(
            '%s.%s' % (module_name, action_name))
        picking = self.sale_id.picking_ids[0]
        picking.pending_signed = 'pending'
        vals['context'] = dict(self.env.context, picking=picking.id)
        return vals

    def action_credit(self):
        return super(
            SaleOrderConfirmAndPay,
            self.with_context(avoid_print_report_picking=True)).action_credit()

    def action_print_picking(self):
        if self.env.context.get('avoid_print_report_picking'):
            return self._reopen_view()
        return super().action_print_picking()
