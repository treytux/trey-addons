# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.one
    def action_paid(self):
        def get_line_index(invoice_line, move_lines, precision):
            for i, move in enumerate(move_lines):
                if (invoice_line.product_id == move.product_id and
                        invoice_line.quantity == round(
                            move.product_qty, precision)):
                    return i

        res = super(PosOrder, self).action_paid()
        if self.session_id.config_id.auto_invoice:
            self.action_invoice()
            self.invoice_id.signal_workflow('invoice_open')
            self.invoice_id.picking_ids = [(6, 0, [self.picking_id.id])]
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            move_lines = list(self.picking_id.move_lines or [])
            for line in self.invoice_id.invoice_line:
                index = get_line_index(line, move_lines, precision)
                move = move_lines.pop(index)
                line.move_line_ids = [(6, 0, [move.id])]
        return res
