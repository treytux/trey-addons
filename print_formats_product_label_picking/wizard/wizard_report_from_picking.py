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
        move_ids = []
        operation_ids = []
        picking_ids = self.env.context['active_ids']
        if self.picking_quantity in ['line', 'one']:
            moves = self.env['stock.move'].search([
                ('picking_id', 'in', picking_ids)])
            move_ids = [m.id for m in moves]
        if self.picking_quantity == 'one':
            [move_ids.append(m.id) for m in moves if m.id not in move_ids]
        elif self.picking_quantity == 'total':
            for picking in self.env['stock.picking'].browse(picking_ids):
                [[operation_ids.append(op.id)
                  for item in range(int(op.product_qty))]
                 for op in picking.pack_operation_ids]
            if not operation_ids:
                raise exceptions.Warning(_(
                    'No operations, to print this type of label you must '
                    'transfer the picking.'))
        if not move_ids and not operation_ids:
            raise exceptions.Warning(_('No labels for print'))
        object_ids = (
            self.picking_quantity == 'total' and operation_ids or move_ids)
        render_func = 'render_product_picking_label'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': self.report_id.report_name,
            'datas': {
                'ids': object_ids,
                'picking_quantity': self.picking_quantity},
            'context': {
                'render_func': render_func,
                'report_name': self.report_id.report_name}}
