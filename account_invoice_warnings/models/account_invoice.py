###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    wrong_taxes = fields.Boolean(
        compute='_compute_wrong_taxes',
    )
    wrong_account = fields.Boolean(
        compute='_compute_wrong_accounts',
    )
    wrong_vat = fields.Boolean(
        compute='_compute_wrong_vat',
    )

    @api.depends('partner_id.vat', 'partner_id.aeat_anonymous_cash_customer')
    def _compute_wrong_vat(self):
        if not self.env.user.company_id.show_wrong_vat:
            return
        for invoice in self:
            if not invoice.partner_id:
                break
            if not invoice.partner_id.vat and not \
                    invoice.partner_id.aeat_anonymous_cash_customer:
                invoice.wrong_vat = True

    @api.depends('invoice_line_ids.invoice_line_tax_ids')
    def _compute_wrong_taxes(self):
        if not self.env.user.company_id.show_wrong_taxes:
            return
        for invoice in self:
            lines = invoice.invoice_line_ids.filtered(
                lambda o: o.display_type not in ('line_section', 'line_note'))
            if not all([x.invoice_line_tax_ids for x in lines]):
                invoice.wrong_taxes = True

    @api.depends('invoice_line_ids.account_id.code')
    def _compute_wrong_accounts(self):
        if not self.env.user.company_id.show_wrong_accounts:
            return
        for invoice in self:
            lines = invoice.invoice_line_ids.filtered(lambda x: x.account_id)
            code = ''
            if invoice.type in ('out_invoice', 'out_refund'):
                code = '7'
            elif invoice.type in ('in_invoice', 'in_refund'):
                code = '6'
            if not all([x.account_id.code.startswith(code) for x in lines]):
                invoice.wrong_account = True
