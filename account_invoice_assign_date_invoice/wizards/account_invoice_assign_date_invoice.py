###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountInvoiceAssignDateInvoice(models.TransientModel):
    _name = 'account.invoice.assign.date.invoice'
    _description = 'Assign Date to Invoice'

    date_invoice = fields.Date(
        string='Date Invoice',
        required=True,
    )

    def assign_values_invoice(self):
        active_ids = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(active_ids)
        invoices_not_draft = False
        raise_text = (_(
            'The following invoices are not in draft state, they can '
            'not be modified:'))
        for invoice in invoices:
            if invoice.state != 'draft':
                invoices_not_draft = True
                raise_text += f'\n{invoice.number}'
            else:
                invoice.date_invoice = self.date_invoice
        if invoices_not_draft:
            raise UserError(raise_text)
