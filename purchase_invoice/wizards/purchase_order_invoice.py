###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api, fields, _


class PurchaseOrderInvoice(models.TransientModel):
    _name = 'purchase.order.invoice'
    _description = 'Purchase order invoice wizard'

    merge_draft_invoice = fields.Boolean(
        string='Merge with draft invoices',
        default=True)

    @api.multi
    def create_invoices(self):
        purchases = self.env['purchase.order'].browse(
            self.env.context.get('active_ids', []))
        purchases.with_context(
            merge_draft_invoice=self.merge_draft_invoice).create_invoices()
        if self._context.get('open_invoices', False):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.invoice',
                'name': _('Generated Invoices'),
                'views': [[False, 'tree'], [False, 'form']],
                'domain': [['id', 'in', purchases.mapped('invoice_ids').ids]]}
        return {'type': 'ir.actions.act_window_close'}
