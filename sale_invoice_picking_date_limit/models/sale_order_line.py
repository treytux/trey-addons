###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_delivery_methods(self):
        self.ensure_one()
        if self.qty_delivered_method != 'stock_move':
            return False
        date_done = self._context.get('transfered_date')
        if not date_done:
            return False
        qty = 0.0
        moves = self.move_ids.filtered(
            lambda m:
                m.state == 'done'
                and m.picking_id.date_done.date() <= date_done
                and not m.scrapped and self.product_id == m.product_id)
        for move in moves:
            if move.location_dest_id.usage == 'customer':
                if not move.origin_returned_move_id \
                   or (move.origin_returned_move_id and move.to_refund):
                    qty += move.product_uom._compute_quantity(
                        move.product_uom_qty, self.product_uom)
            elif move.location_dest_id.usage != 'customer' and move.to_refund:
                qty -= move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom)
        return qty, self.move_ids - moves

    def invoice_line_create_vals(self, invoice_id, qty):
        res = super().invoice_line_create_vals(invoice_id, qty)
        if not self._context.get('transfered_date'):
            return res
        for line in self:
            if line.qty_delivered_method != 'stock_move':
                continue
            qty_new, moves = line._get_delivery_methods()
            if qty_new is False or qty == qty_new:
                continue
            for ln in res:
                if line.id in ln['sale_line_ids'][0][2]:
                    ln['quantity'] = qty_new - line.qty_invoiced
                    ln['move_line_ids'] = [
                        m for m in ln['move_line_ids']
                        if m[1] not in moves.ids]
                    break
        return res
