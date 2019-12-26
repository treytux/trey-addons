###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo import _, api, exceptions, fields, models


class WizCreateInvoice(models.TransientModel):
    _name = 'wiz.print.options.account.subvention.report'
    _description = 'Wizard to report subvention'

    trimester = fields.Selection(
        selection=[
            (1, 'Trimester 1'),
            (2, 'Trimester 2'),
            (3, 'Trimester 3'),
            (4, 'Trimester 4'),
        ],
        default=1,
        required=1,
    )
    fiscal_year = fields.Many2one(
        comodel_name='account.fiscal.year',
        required=1,
    )

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
            account_invoice = account_move_line.invoice_id
            month = (account_invoice and account_invoice.date_invoice) and \
                account_invoice.date_invoice.month or -1
            year = (account_invoice and account_invoice.date_invoice) and \
                account_invoice.date_invoice.year or -1
            if year != target_year:
                continue
            numbers = []
            if self.month_in_trimester(month, trimester):
                if not account_move_line.invoice_id:
                    raise exceptions.Warning(_(
                        'ERROR: Account move line %s has not'
                        'associated invoices') % account_move_line.name)
                invoice_line = account_move_line.invoice_id.invoice_line_ids[0]
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
                        'creation_date': fields.Date.to_string(
                            account_move_line.create_date),
                        'subvs': {},
                        'number': int(
                            account_move_line.partner_id.street[21:24]),
                        'subv_imports': {}})
                numbers.append(int(account_move_line.partner_id.street[21:24]))
                partner_id = expedients[expedient_id]['partners'][
                    account_move_line.partner_id.id]
                amount_total = False
                for invoice_line in \
                        account_move_line.invoice_id.invoice_line_ids:
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

    def _prepare_report_data(self):
        subvention = self.env['account.subvention'].browse(
            self.env.context.get('active_ids', []))
        data = {
            'ids': [],
            'model': 'account.subvention',
            'form': self.env.context.get('active_ids', []),
            'trimester': self.trimester,
            'month_labels': self.get_month_labels(self.trimester),
            'expedients': self.get_expedients(
                subvention, self.trimester, self.fiscal_year.date_from.year,
            ),
        }
        return data

    @api.multi
    def button_print(self):
        self.ensure_one()
        subventions = self.env.context.get('active_ids', [])
        datas = self._prepare_report_data()
        return self.env.ref(
            'account_subvention.subvention_report_create'
        ).report_action(subventions, data=datas)
