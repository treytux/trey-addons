###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res = super().invoice_validate()
        for invoice in self:
            sale_order = self.env['sale.order'].search([
                ('name', '=', invoice.origin),
            ], limit=1)
            website = sale_order and sale_order.website_id or None
            state = invoice.state
            if (
                    website and sale_order.website_id.notify_invoice_open
                    and state == 'open'):
                invoice.message_post_with_template(
                    self.env.ref('account.email_template_edi_invoice').id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res
