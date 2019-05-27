###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class AccountAnalyticAccount(models.Model):
    _inherit = ['account.analytic.account']

    recurring_reference = fields.Char(
        string='Invoice Reference',
        help='The partner reference of this invoice. You can use: '
             '`#MONTH_INT#`, `#MONTH_STR#` or `#YEAR_INT#`')
    recurring_negative = fields.Integer(
        string='Negative Days',
        help='Real generate invoice(End Date - Negative Days in days)',
        default=15)
    is_custom_reference = fields.Boolean(string='Custom Reference?')

    @api.model
    def _insert_markers(self, line, date_format):
        name = super(AccountAnalyticAccount, self)._insert_markers(
            line, date_format)
        date_to = fields.Date.from_string(line.date_to)
        name = name.replace('#MONTH_INT#', date_to.strftime('%m'))
        name = name.replace('#MONTH_STR#', date_to.strftime('%B').capitalize())
        name = name.replace('#YEAR_INT#', date_to.strftime('%Y'))
        return name

    @api.model
    def _insert_custom_ref(self, invoice):
        return self.recurring_reference

    @api.multi
    def _create_invoice(self, invoice=False):
        self.ensure_one()
        invoice = super(AccountAnalyticAccount, self)._create_invoice(invoice)
        if invoice and invoice.state == 'draft' and self.is_custom_reference:
            invoice.name = self._insert_custom_ref(invoice)
        return invoice

    @api.model
    def cron_recurring_create_invoice(self):
        self.env.cr.execute("""
        SELECT id
        FROM account_analytic_account
        WHERE recurring_invoices is True
        AND date_end >= NOW() OR date_end is null
        AND (recurring_next_date -
        interval '1 day' * recurring_negative) <= NOW();
        """)
        contracts = self.browse([r[0] for r in self.env.cr.fetchall()])
        return contracts.with_context(cron=True).recurring_create_invoice()
