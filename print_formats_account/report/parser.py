###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from collections import OrderedDict

from odoo import api, models
from odoo.tools import float_is_zero


class ReportAccountReportInvoiceBase(models.AbstractModel):
    _name = 'report.account.report_invoice_base'
    _description = 'Report Invoice Base'

    @api.model
    def _sort_grouped_lines(self, lines_dic):
        return sorted(lines_dic, key=lambda x: (
            x['picking'].date, x['picking'].date_done))

    def _get_signed_quantity_done(self, invoice_line, move, sign):
        qty = 0
        if move.location_id.usage == 'customer':
            qty = -move.quantity_done * sign
        elif move.location_dest_id.usage == 'customer':
            qty = move.quantity_done * sign
        return qty

    def get_lines_grouped(self, invoice):
        if not invoice.company_id.invoice_report_group_by:
            return [
                {'picking': False, 'line': line, 'quantity': line.quantity}
                for line in invoice.invoice_line_ids
            ]
        picking_dict = OrderedDict()
        lines_dict = OrderedDict()
        sign = -1.0 if invoice.type == 'out_refund' else 1.0
        pickings = invoice.mapped('invoice_line_ids.move_line_ids.picking_id')
        so_dict = {x.sale_id: x for x in pickings if x.sale_id}
        for line in invoice.invoice_line_ids:
            remaining_qty = line.quantity
            for move in line.move_line_ids:
                key = (move.picking_id, line)
                picking_dict.setdefault(key, 0)
                qty = self._get_signed_quantity_done(line, move, sign)
                picking_dict[key] += qty
                remaining_qty -= qty
            if not line.move_line_ids and line.sale_line_ids:
                for so_line in line.sale_line_ids:
                    if so_dict.get(so_line.order_id):
                        key = (so_dict[so_line.order_id], line)
                        picking_dict.setdefault(key, 0)
                        qty = so_line.product_uom_qty
                        picking_dict[key] += qty
                        remaining_qty -= qty
            if (not float_is_zero(
                    remaining_qty,
                    precision_rounding=line.product_id.uom_id.rounding)):
                lines_dict[line] = remaining_qty
        no_picking = [
            {'picking': False, 'line': key, 'quantity': value}
            for key, value in lines_dict.items()
        ]
        with_picking = [
            {'picking': key[0], 'line': key[1], 'quantity': value}
            for key, value in picking_dict.items()
        ]
        return no_picking + self._sort_grouped_lines(with_picking)

    @api.multi
    def get_payment_terms(self, invoice):
        if not invoice.payment_term_id:
            return []
        if not invoice.move_id and not invoice.move_id.line_ids:
            return []
        payment_terms = [
            (line.date_maturity, max(line.debit, line.credit))
            for line in invoice.move_id.line_ids
            if line.account_id == invoice.account_id]
        payment_terms.sort()
        return payment_terms

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.invoice'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'account.invoice',
            'docs': docs,
            'get_lines_grouped': self.get_lines_grouped,
            'get_payment_terms': self.get_payment_terms}


class ReportAccountReportInvoice(ReportAccountReportInvoiceBase):
    _name = 'report.account.report_invoice'
    _description = 'Report Invoice'


class ReportAccountReportInvoiceWithPayments(ReportAccountReportInvoiceBase):
    _name = 'report.account.report_invoice_with_payments'
    _description = 'Report Invoice with payments'
