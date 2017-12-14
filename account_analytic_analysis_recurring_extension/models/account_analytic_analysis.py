# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import api, models, fields
from datetime import datetime


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    recurring_reference = fields.Char(
        string='Invoice Reference',
        help='The partner reference of this invoice. You can use: '
             '`#MONTH_INT#`, `#MONTH_STR#` or `#YEAR_INT#`')
    recurring_negative = fields.Integer(
        string='Negative Days',
        help='Real generate invoice(End Date - Negative Days in days)',
        default=15)

    @api.model
    def _cron_recurring_create_invoice(self):
        self.env.cr.execute('''SELECT id
            FROM account_analytic_account
            WHERE recurring_invoices is True
                AND state = 'open'
                AND type = 'contract'
                AND (recurring_next_date
                     - interval '1 day' * recurring_negative) <= NOW()
                ;''')
        recurring = self.browse([r[0] for r in self.env.cr.fetchall()])
        invoice_ids = recurring._recurring_create_invoice()
        invoices = self.env['account.invoice'].browse(invoice_ids)
        return invoices

    @api.model
    def _prepare_invoice_data(self, contract):
        invoice = super(AccountAnalyticAccount,
                        self)._prepare_invoice_data(contract)
        # Force Spanish locale for translation
        import locale
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        if contract.recurring_invoices:
            end_date = datetime.strptime(contract.recurring_next_date,
                                         '%Y-%m-%d')
            reference = contract.recurring_reference or ''
            # Cambiar #END_MONTH_INT# por Mes en Entero
            reference = reference.replace(
                '#MONTH_INT#',
                end_date.strftime('%m')
            )
            # Cambiar #END_MONTH_STR# por mes en texto
            reference = reference.replace(
                '#MONTH_STR#',
                str(end_date.strftime('%B')).capitalize()
            )
            # Cambiar #END_YEAR_INT# por año en numero
            reference = reference.replace(
                '#YEAR_INT#',
                end_date.strftime('%Y')
            )
            invoice['name'] = reference
            invoice['reference'] = reference
        return invoice

    @api.model
    def prepare_invoice_lines(self, contract, fiscal_position_id):
        invoice_lines = super(AccountAnalyticAccount,
                              self).prepare_invoice_lines(contract,
                                                          fiscal_position_id)
        if contract.type == 'contract':
            fiscal_position = None
            fpos_obj = self.env['account.fiscal.position']
            if fiscal_position_id:
                fiscal_position = fpos_obj.browse(fiscal_position_id)
            for line in invoice_lines:
                tax_ids = line[2]['invoice_line_tax_id']
                if tax_ids:
                    tax_ids = tax_ids[0][2]
                    tax_ids = self.env['account.tax'].search(
                        [('id', 'in', tax_ids),
                         ('company_id', '=', contract.company_id.id)])
                    taxes = self.env['account.tax'].browse(tax_ids)
                    tax_ids = fpos_obj.map_tax(fiscal_position, taxes)
                    line[2]['invoice_line_tax_id'] = [(6, 0, tax_ids)]
        return invoice_lines

    @api.multi
    def _recurring_create_invoice(self, automatic=False):
        '''Inherit for calculate taxes.'''
        invoice_ids = super(
            AccountAnalyticAccount, self)._recurring_create_invoice(
            automatic=automatic)
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            invoice.button_compute()
        return invoice_ids
