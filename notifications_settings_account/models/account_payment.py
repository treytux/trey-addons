###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def action_validate_invoice_payment(self):
        res = super().action_validate_invoice_payment()
        for payment in self:
            invoice = payment.invoice_ids
            sale_order = self.env['sale.order'].search([
                ('name', '=', invoice.origin),
            ], limit=1)
            website = sale_order and sale_order.website_id or None
            if website and sale_order.website_id.notify_invoice_paid:
                invoice.message_post_with_template(
                    self.env.ref('account.email_template_edi_invoice').id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res
