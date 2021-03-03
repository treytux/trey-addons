###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange('is_email')
    def _compute_invoice_without_email(self):
        super()._compute_invoice_without_email()
        for wizard in self:
            if wizard.invoice_without_email is not False:
                active_invoices = self.env['account.invoice'].search([
                    ('id', 'in', self.env.context.get('active_ids')),
                ])
                invoices = []
                for i in active_invoices:
                    if not any([
                        f.partner_id.email is not False
                            for f in i.message_follower_ids]):
                        invoices.append(i)
                if len(invoices) > 0:
                    wizard.invoice_without_email = "%s\n%s" % (
                        _(
                            "The following invoice(s) will not be sent by"
                            " email, because some followers don't have email"
                            " address."
                        ),
                        '\n'.join([
                            i.reference or i.display_name for i in invoices])
                    )
                else:
                    wizard.invoice_without_email = False
