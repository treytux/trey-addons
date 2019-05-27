# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from functools import partial
from openerp import api, exceptions, models, _
import datetime


class AcountSubvention(models.TransientModel):
    _name = 'report.account_subvention.subvention_report'

    @api.model
    def month_in_trimester(self, month, trimester):
        return (month - 1) // 3 + 1 == trimester

    @api.model
    def get_month_labels(self, trimester):
        months_labels = {}
        for month in range(((trimester - 1) * 3) + 1, (trimester * 3) + 1):
            months_labels[month] = str.capitalize(datetime.date(
                1900, month, 1).strftime('%B'))
        months = sorted(months_labels)
        return [months_labels[key] for key in months]

    @api.model
    def get_months_index(self, trimester):
        months_index = {}
        for month in range(((trimester - 1) * 3) + 1, (trimester * 3) + 1):
            months_index[month] = False
        return months_index

    @api.model
    def get_expedients(self, subvention, trimester, target_year):
        expedients = {}
        addresses_sorted = []
        for account_move_line in subvention.account_move_line_ids:
            account_invoice = account_move_line.invoice
            month = (account_invoice and account_invoice.date_invoice) and int(
                account_invoice.date_invoice[5:7]) or -1
            year = (account_invoice and account_invoice.date_invoice) and int(
                account_invoice.date_invoice[0:4]) or -1
            if year != target_year:
                continue
            numbers = []
            if self.month_in_trimester(month, trimester):
                if not account_move_line.invoice:
                    raise exceptions.Warning(_(
                        'ERROR: Account move line %s has not'
                        'associated invoices') % account_move_line.name)
                invoice_line = account_move_line.invoice.invoice_line[0]
                expedient_id = (
                    invoice_line.account_analytic_id and
                    invoice_line.account_analytic_id.parent_id and
                    invoice_line.account_analytic_id.parent_id.id or -1)
                expedient_name = (
                    invoice_line.account_analytic_id and
                    invoice_line.account_analytic_id.parent_id and
                    invoice_line.account_analytic_id.parent_id.name or
                    'No expedient')
                expedients.setdefault(expedient_id, {
                    'name': expedient_name,
                    'addresses_sorted': [],
                    'partners': {},
                    'exp_total': False})
                if not account_move_line.partner_id:
                    raise exceptions.Warning(_(
                        'ERROR: Account move line %s has not associated '
                        'partner') % account_move_line.name)
                expedients[expedient_id]['partners'].setdefault(
                    account_move_line.partner_id.id, {
                        'partner': account_move_line.partner_id,
                        'months': self.get_months_index(trimester),
                        'creation_date': account_move_line.date_created,
                        'subvs': {},
                        'number': int(
                            account_move_line.partner_id.street[21:24]),
                        'subv_imports': {}})
                numbers.append(int(account_move_line.partner_id.street[21:24]))
                partner_id = expedients[expedient_id]['partners'][
                    account_move_line.partner_id.id]
                amount_total = False
                for invoice_line in account_move_line.invoice.invoice_line:
                    if invoice_line.subvention_id:
                        amount_total += invoice_line.price_subtotal
                partner_id['months'].update({month: amount_total})
                partner_id['subvs'].update({
                    month: account_move_line.subvention_percent})
                partner_id['subv_imports'].update({
                    month: (amount_total *
                            account_move_line.subvention_percent / 100)})
                expedients[expedient_id]['exp_total'] += partner_id[
                    'subv_imports'][month]
                for key in numbers:
                    if key not in addresses_sorted:
                        addresses_sorted.append(key)
                addresses_sorted = sorted(addresses_sorted)
                expedients[expedient_id]['addresses_sorted'] = addresses_sorted
        expedients = expedients.values()
        for expedient in expedients:
            expedient['partners'] = expedient['partners'].values()
        return expedients

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        subvention_obj = self.env['account.subvention']
        report = report_obj._get_report_from_name(
            'account_subvention.subvention_report')
        docs = subvention_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': docs,
            'get_expedients': partial(self.get_expedients),
            'get_month_labels': partial(self.get_month_labels),
            'trimester': data['trimester'],
            'target_year': data['target_year']}
        report = report_obj.browse(self.ids[0])
        return report.render('account_subvention.subvention_report', docargs)
