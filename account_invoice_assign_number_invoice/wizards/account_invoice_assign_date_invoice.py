###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountInvoiceAssignNumberInvoice(models.TransientModel):
    _inherit = 'account.invoice.assign.date.invoice'

    number_invoice = fields.Char(
        string='Invoice Number'
    )

    def assign_values_invoice(self):
        if not self.number_invoice:
            return super().assign_values_invoice()
        self.assign_number_invoice()

    def assign_number_invoice(self):
        active_ids = self.env.context.get('active_ids', [])
        invoice = self.env['account.invoice'].browse(active_ids)
        if len(invoice) > 1:
            raise_text = (_(
                'If you want to change a invoice number, you can\'t select '
                'more than one invoice'))
            raise UserError(raise_text)
        if invoice.state != 'draft':
            raise_text = (_(
                'The invoice isn\'t in draft state, it can\'t be modified'))
            raise UserError(raise_text)
        invoice.write({
            'date_invoice': self.date_invoice,
            'number': self.number_invoice,
            'invoice_number': self.number_invoice,
        })
