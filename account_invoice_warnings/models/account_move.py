###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    wrong_taxes = fields.Boolean(
        compute='_compute_wrong_taxes',
    )
    wrong_account = fields.Boolean(
        compute='_compute_wrong_accounts',
    )
    wrong_vat = fields.Boolean(
        compute='_compute_wrong_vat',
    )

    @api.depends(
        'company_id.show_wrong_vat', 'partner_id.vat',
        'partner_id.aeat_anonymous_cash_customer')
    def _compute_wrong_vat(self):
        invoice_types = [
            'out_invoice', 'out_refund', 'in_invoice', 'in_refund']
        for invoice in self:
            invoice.wrong_vat = False
            if not invoice.company_id.show_wrong_vat:
                continue
            if not invoice.partner_id:
                continue
            if invoice.move_type not in invoice_types:
                continue
            if not invoice.partner_id.vat and not \
                    invoice.partner_id.aeat_anonymous_cash_customer:
                invoice.wrong_vat = True

    @api.depends('company_id.show_wrong_taxes', 'invoice_line_ids.tax_ids')
    def _compute_wrong_taxes(self):
        invoice_types = [
            'out_invoice', 'out_refund', 'in_invoice', 'in_refund']
        for invoice in self:
            invoice.wrong_taxes = False
            if not invoice.company_id.show_wrong_taxes:
                continue
            if invoice.move_type not in invoice_types:
                continue
            lines = invoice.invoice_line_ids.filtered(
                lambda o: o.display_type not in ('line_section', 'line_note'))
            if not all([x.tax_ids for x in lines]):
                invoice.wrong_taxes = True

    @api.depends(
        'company_id.show_wrong_accounts', 'invoice_line_ids.account_id.code')
    def _compute_wrong_accounts(self):
        invoice_types = [
            'out_invoice', 'out_refund', 'in_invoice', 'in_refund']
        for invoice in self:
            invoice.wrong_account = False
            if not invoice.company_id.show_wrong_accounts:
                continue
            if invoice.move_type not in invoice_types:
                continue
            lines = invoice.invoice_line_ids.filtered(lambda x: x.account_id)
            code = ''
            if invoice.move_type in ('out_invoice', 'out_refund'):
                code = '7'
            elif invoice.move_type in ('in_invoice', 'in_refund'):
                code = '6'
            if not all([x.account_id.code.startswith(code) for x in lines]):
                invoice.wrong_account = True
