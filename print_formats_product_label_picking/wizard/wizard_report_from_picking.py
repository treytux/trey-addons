# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, _, exceptions


class WizProductLabelFromPicking(models.TransientModel):
    _inherit = 'wiz.product.label'

    picking_quantity = fields.Selection(
        selection=[
            ('one', 'One label for each product'),
            ('line', 'One label for each line'),
            ('total', 'Total product quantity')],
        string='Quantity',
        default='total')

    @api.multi
    def button_print_from_picking(self):
        moves = self.env['stock.move'].search(
            [('picking_id', 'in', self.env.context['active_ids'])])
        picking = self.env['stock.picking'].browse(
            self.env.context['active_ids'][0])
        move_ids = []
        op_ids = []
        if self.picking_quantity == 'line':
            move_ids = [m.id for m in moves]
        elif self.picking_quantity == 'total':
            for op in picking.pack_operation_ids:
                op_ids = op_ids + (
                    [op.id] * int(op.product_qty))
            if not op_ids:
                raise exceptions.Warning(_(
                    'No operations, to print this type of label you must '
                    'transfer the picking.'))
        elif self.picking_quantity == 'one':
            for m in moves:
                if m.id not in move_ids:
                    move_ids.append(m.id)
        if not move_ids and not op_ids:
            raise exceptions.Warning(_('No labels for print'))
        cr, uid, context = self.env.args
        if self.picking_quantity == 'total':
            ids = op_ids
        else:
            ids = move_ids
        return {
            'type': 'ir.actions.report.xml',
            'report_name': self.report_id.report_name,
            'datas': {
                'ids': ids,
                'picking_quantity': self.picking_quantity},
            'context': {
                'render_func': 'render_product_picking_label',
                'report_name': self.report_id.report_name
            }
        }
