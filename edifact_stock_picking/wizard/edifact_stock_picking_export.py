# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class EdifactStockPickingExport(models.TransientModel):
    _name = 'edifact.stock.picking.export'
    _description = 'Export Stock Pickings to EDI'

    @api.model
    def _get_default_pickings(self):
        if not self.env.context:
            return
        model = self.env.context.get('active_model', '')
        if model == 'stock.picking':
            return [(6, 0, self.env.context.get('active_ids', []))]
        return

    picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        domain=[('picking_type_id.code', '=', 'outgoing'),
                ('state', '!=', 'cancel')],
        default=_get_default_pickings)

    @api.multi
    def action_export(self):
        edi_doc = self.env['edifact.document'].process_picking_out_files(
            self.picking_ids)
        if not edi_doc:
            return
        value = {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'edifact.document',
            'res_id': edi_doc.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }
        return value
