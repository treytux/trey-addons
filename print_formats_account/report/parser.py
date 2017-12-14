# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
from functools import partial
from datetime import datetime
import time


class InvoiceReport(models.TransientModel):
    _name = 'report.account.report_invoice'

    @api.multi
    def get_tax_amount(self, invoice_type, tax_code_id):
        if invoice_type in ('in_invoice', 'out_invoice'):
            domain = [('tax_code_id', '=', tax_code_id)]
        else:
            domain = [('ref_tax_code_id', '=', tax_code_id)]
        tax = self.env['account.tax'].search(domain)
        if tax:
            return tax[0].amount * 100
        return None

    @api.multi
    def get_tax_description(self, tax_line_name):
        tax_line_name_parts = tax_line_name.split('-')
        if len(tax_line_name_parts) > 0:
            return tax_line_name_parts[0]
        else:
            return tax_line_name

    @api.multi
    def get_taxes(self, invoice):
        taxes = {}
        for line in invoice.invoice_line:
            for tax in line.invoice_line_tax_id:
                t = tax.compute_all(
                    line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                    line.product_uom_qty,
                    line.product_id,
                    line.invoice_id.partner_id
                )['taxes']
                if len(t) > 0 and t[0]['name'] not in taxes:
                    taxes[t[0]['name']] = 0
                taxes[t[0]['name']] += t[0]['amount']
        return taxes

    @api.multi
    def hide_account_number(self, mandate_id):
        '''Oculta los digitos de control y los cuatro ultimos numeros de la
        cuenta bancaria del mandato.
        '''
        if not mandate_id.exists():
            return ''
        elif mandate_id.partner_bank_id.acc_number:
            acc_number = mandate_id.partner_bank_id.acc_number
            return acc_number.replace(acc_number[15:17], '**').replace(
                acc_number[-4:], '****')

    @api.multi
    def monetary_format(self, string, context=None):
        formated = ('%.2f' % (string,))
        # formated = ('%.2f' % (string,)).rstrip('0').rstrip('.')
        formated = formated.replace('.', ',')
        return formated

    @api.model
    def str_to_date(self, string_date):
        return time.strftime('%d/%m/%Y',
                             time.strptime(string_date, '%Y-%m-%d'))

    @api.multi
    def get_payment_terms(self, invoice):
        payment_terms = []
        if not invoice.payment_term:
            return payment_terms
        if not invoice.move_id and not invoice.move_id.line_id:
            return payment_terms
        for l in invoice.move_id.line_id:
            if l.date_maturity:
                payment_terms.append((
                    l.date_maturity,
                    l.debit > 0 and l.debit or l.credit
                ))
        payment_terms.sort()

        return payment_terms

    @api.multi
    def get_lines_grouped_by_picking(self, invoice):
        pickings = [l.move_line_ids[0].picking_id
                    for l in invoice.invoice_line
                    if l.move_line_ids and l.move_line_ids[0].picking_id]
        moves = {p.id: p for p in list(set(pickings))}
        moves[0] = None
        lines = {k: [] for k in moves.keys()}
        for line in invoice.invoice_line:
            move = line.move_line_ids and line.move_line_ids[0] or None
            picking = (move and move.picking_id) and move.picking_id or None
            lines[picking and picking.id or 0].append(line)

        def sorted_lines(x, y):
            xmove = x.move_line_ids and x.move_line_ids[0].id or x.sequence
            ymove = y.move_line_ids and y.move_line_ids[0].id or y.sequence
            return xmove - ymove

        for k, v in lines.iteritems():
            v.sort(cmp=sorted_lines)

        def sorted_picking(x, y):
            ndate = datetime.now()
            xdate = x[0] and fields.Datetime.from_string(x[0]) or ndate
            ydate = y[0] and fields.Datetime.from_string(y[0]) or ndate
            return xdate > ydate and 1 or -1

        picking_sort = [(k and v.date_done or None, k)
                        for k, v in moves.iteritems()]
        picking_sort.sort(cmp=sorted_picking)

        return [moves, lines, [p[1] for p in picking_sort]]

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        invoice_obj = self.env['account.invoice']
        report = report_obj._get_report_from_name('account.report_invoice')
        selected_invoices = invoice_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_invoices,
            'get_tax_amount': partial(self.get_tax_amount),
            'get_tax_description': partial(self.get_tax_description),
            'get_taxes': partial(self.get_taxes),
            'hide_account_number': partial(self.hide_account_number),
            'monetary_format': partial(self.monetary_format),
            'str_to_date': partial(self.str_to_date),
            'get_payment_terms': partial(self.get_payment_terms),
            'get_lines_grouped_by_picking': partial(
                self.get_lines_grouped_by_picking)}
        report = report_obj.browse(self.ids[0])
        return report.render('account.report_invoice', docargs)
