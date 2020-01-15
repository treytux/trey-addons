###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, api


class ReportAccountReportInvoiceBase(models.AbstractModel):
    _name = 'report.account.report_invoice_base'
    _description = 'Report Invoice Base'

    def _group_lines(self, lines, fnc_get_record):
        res = []
        for line in lines:
            record = fnc_get_record(line)
            last_record = res and fnc_get_record(res[-1:][0]) or None
            if record != last_record:
                res.append(record)
            res.append(line)
        return res

    def _sort_line_sale(self, line):
        sale = (
            line.sale_line_ids and line.sale_line_ids[0].order_id or None)
        return sale and sale.name or 'no-sale'

    @api.multi
    def get_lines_grouped_by_sale(self, invoice):
        lines = invoice.invoice_line_ids.sorted(self._sort_line_sale)
        return self._group_lines(lines, lambda line: (
            line.sale_line_ids and line.sale_line_ids[0].order_id or None))

    def _sort_line_purchase(self, line):
        purchase = (
            line.purchase_line_id and
            line.purchase_line_id.order_id or None)
        return purchase and purchase.name or 'no-purchase'

    @api.multi
    def get_lines_grouped_by_purchase(self, invoice):
        lines = invoice.invoice_line_ids.sorted(self._sort_line_purchase)
        return self._group_lines(lines, lambda line: (
            line.purchase_line_id and line.purchase_line_id.order_id or None))

    def _get_picking_from_invoice_line(self, line):
        if not line.sale_line_ids or not line.sale_line_ids[0].move_ids:
            return None
        pickings = [
            m.picking_id for m in line.sale_line_ids[0].move_ids
            if m.state == 'done']
        return pickings and pickings[-1:][0] or None

    def _sort_line_picking(self, line):
            picking = self._get_picking_from_invoice_line(line)
            return picking and picking[0].name or 'no-picking'

    @api.multi
    def get_lines_grouped_by_picking(self, invoice):
        lines = invoice.invoice_line_ids.sorted(self._sort_line_picking)
        return self._group_lines(lines, self._get_picking_from_invoice_line)

    @api.multi
    def get_lines_grouped_by(self, invoice):
        if invoice.company_id.invoice_report_group_by == 'order':
            if invoice.type in ['out_invoice', 'out_refund']:
                return self.get_lines_grouped_by_sale(invoice)
            return self.get_lines_grouped_by_purchase(invoice)
        elif invoice.company_id.invoice_report_group_by == 'picking':
            return self.get_lines_grouped_by_picking(invoice)
        return invoice.invoice_line_ids

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
            'get_lines_grouped_by': self.get_lines_grouped_by,
            'get_payment_terms': self.get_payment_terms}


class ReportAccountReportInvoice(ReportAccountReportInvoiceBase):
    _name = 'report.account.report_invoice'
    _description = 'Report Invoice'


class ReportAccountReportInvoiceWithPayments(ReportAccountReportInvoiceBase):
    _name = 'report.account.report_invoice_with_payments'
    _description = 'Report Invoice with payments'
