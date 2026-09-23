###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    has_sale_session = fields.Boolean(
        string='Invoice created from sale session',
    )

    def print_invoice_report_and_payment_sale_session_cashdro(self):
        sale = self.env['sale.order'].browse(self.env.context['sale_id'])
        session = self.env['sale.session'].browse(
            self.env.context['session_id'])
        journal = self.env['account.journal'].browse(
            self.env.context['journal_id'])
        payment = self.env['account.payment'].create({
            'partner_id': sale.invoice_ids[0].partner_id.id,
            'invoice_ids': [(6, 0, sale.invoice_ids.ids)],
            'sale_session_id': session.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'amount': sale.invoice_ids[0].amount_total,
            'communication': '[%s] %s: %s' % (
                session.name, sale.name, sale.invoice_ids[-1:].name),
            'journal_id': journal.id,
        })
        payment.action_validate_invoice_payment()
        team_journal = session.team_id.simplified_journal_id
        if team_journal == sale.invoice_ids.journal_id:
            report = self.env.ref(
                'print_formats_account_ticket.'
                'report_account_invoice_ticket_create')
            return report.report_action(sale.invoice_ids)
        report = self.env.ref('account.account_invoices')
        return report.report_action(sale.invoice_ids)

    def action_open_payment_invoice_with_cashdro(self):
        self.ensure_one()
        action = self.env.ref(
            'sale_session_cashdro.account_invoice_payment_cashdro_action')
        action = action.read()[0]
        return action
