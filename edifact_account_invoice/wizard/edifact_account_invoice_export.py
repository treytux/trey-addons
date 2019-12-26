# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class EdifactAccountInvoiceExport(models.TransientModel):
    _name = 'edifact.account.invoice.export'
    _description = 'Export Invoices to EDI'

    @api.model
    def _get_default_invoices(self):
        if not self.env.context:
            return
        model = self.env.context.get('active_model', '')
        if model == 'account.invoice':
            return [(6, 0, self.env.context.get('active_ids', []))]
        return

    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        domain=[('type', '=', 'out_invoice'),
                ('state', '!=', 'cancel')],
        default=_get_default_invoices)

    @api.multi
    def action_export(self):
        edi_doc = self.env['edifact.document'].process_invoice_out_files(
            self.invoice_ids)
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
