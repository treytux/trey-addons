###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _compute_qty_to_invoice(self):
        super()._compute_qty_to_invoice()
        if not self or self[0].order_id.invoice_policy != 'order':
            return
        other_lines = self.filtered(
            lambda ln: ln.product_id.type == 'service'
            or not ln.order_id.invoice_policy
        )
        for line in self - other_lines:
            if 'done' not in line.move_ids.mapped('state'):
                continue
            line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
        return True
