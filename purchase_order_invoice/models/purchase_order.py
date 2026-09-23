###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.tools.float_utils import float_compare


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_create_invoice(self):
        wizard = self.env['purchase.order.invoice'].with_context(
            active_id=self._context.get('active_id'),
            active_ids=self._context.get('active_ids')
        ).create({})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.invoice',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
            'context': {
                'active_id': self._context.get('active_id'),
            },
        }

    def _get_invoiced(self):
        res = super()._get_invoiced()
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.invoice_status = 'no'
                continue
            if any(
                float_compare(
                    line.qty_invoiced, line.product_qty
                    if line.product_id.purchase_method == 'purchase' else
                    line.qty_received, precision_digits=precision) == -1
                    for line in order.order_line):
                order.invoice_status = 'to invoice'
            elif all(
                float_compare(
                    line.qty_invoiced, line.product_qty
                    if line.product_id.purchase_method == 'purchase' else
                    line.qty_received, precision_digits=precision) >= 0
                    for line in order.order_line) and order.invoice_ids:
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'
        return res
