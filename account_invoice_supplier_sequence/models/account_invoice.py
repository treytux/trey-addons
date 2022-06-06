###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_onchange_create(self):
        res = super()._get_onchange_create()
        res['_onchange_partner_id'].append('reference')
        return res

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super()._onchange_partner_id()
        for invoice in self:
            if invoice.type != 'in_invoice':
                continue
            if invoice.reference:
                continue
            sequence = invoice.partner_id.invoice_supplier_sequence_id
            if not sequence:
                continue
            sequence = sequence.with_context(
                ir_sequence_date=invoice.date or invoice.date_invoice,
                ir_sequence_date_range=invoice.date or invoice.date_invoice,
            )
            invoice.reference = sequence.next_by_id()
