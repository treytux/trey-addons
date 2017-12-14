# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models
import logging
_log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def do_merge(self, keep_references=True, date_invoice=False):
        invoices_info = super(AccountInvoice, self).do_merge(
            keep_references=keep_references, date_invoice=date_invoice)
        for invoice_id, old_invoice_ids in invoices_info.iteritems():
            new_invoice = self.browse(invoice_id)
            old_invoices = self.browse(old_invoice_ids)
            self.merge_lines(new_invoice, old_invoices)
        return invoices_info

    @api.multi
    def merge_lines(self, new_invoice, invoices):
        def _get_line_domain(line):
            domain = []
            line_fields = self._get_invoice_line_key_cols()
            for fname in line_fields:
                condition = '='
                value = getattr(line, fname)
                field = line._fields[fname]
                if field.type in ('many2one'):
                    value = value.id
                elif field.type in ('one2many', 'many2many'):
                    condition = 'in'
                    value = [v.id for v in value]
                domain.append((fname, condition, value))
            return domain

        line_ids = []
        for i in invoices:
            line_ids += i.invoice_line.ids
        old_lines = self.env['account.invoice.line'].browse(line_ids)

        invoices_info = {new_invoice.id: invoices.ids}
        old_pickings = []
        for invoice_id, old_invoice_ids in invoices_info.iteritems():
            for old_line in old_lines:
                for move in old_line.move_line_ids:
                    domain = [('invoice_id', '=', invoice_id)]
                    domain += _get_line_domain(old_line)
                    new_line = self.env['account.invoice.line'].search(domain)
                    if new_line:
                        if not new_line.move_line_ids:
                            new_line.move_line_ids = [(6, 0, [move.id])]
                        move.invoice_line_id = new_line.id
                    if move.picking_id not in old_pickings:
                        old_pickings.append(move.picking_id)
        new_invoice.picking_ids = [(4, p.id) for p in old_pickings]
        return invoices_info
