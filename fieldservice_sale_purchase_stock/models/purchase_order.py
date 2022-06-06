###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def prepare_fsm_values_for_stock_move(self, fsm_order):
        return {
            'fsm_order_id': fsm_order.id,
        }

    def prepare_fsm_values_for_stock_picking(self, fsm_order):
        return {
            'fsm_order_id': fsm_order.id,
        }

    def _link_pickings_to_fsm(self):
        for rec in self:
            sale_ids = self.env['purchase.order'].get_sale_order_ids(rec)
            if not sale_ids:
                continue
            fsm_order = self.env['fsm.order'].search([
                ('sale_id', '=', sale_ids[0]),
                ('sale_line_id', '=', False),
            ])
            for picking in rec.picking_ids:
                picking.write(
                    rec.prepare_fsm_values_for_stock_picking(fsm_order))
                for move in picking.move_lines:
                    move.write(
                        rec.prepare_fsm_values_for_stock_move(fsm_order))

    def button_confirm(self):
        res = super().button_confirm()
        self._link_pickings_to_fsm()
        return res
