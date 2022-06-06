###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def force_quotation_send(self):
        if (not self.website_id or self.website_id.notify_quotation
                or self.state != 'draft'):
            return super().force_quotation_send()
        self.write({
            'state': 'sent'
        })
        self.message_subscribe(self.partner_id.ids)
        return True

    def action_confirm(self):
        this = self.with_context(send_email=self.website_id.notify_sale)
        return super(SaleOrder, this).action_confirm()

    def action_cancel(self):
        res = super().action_cancel()
        template = self.env.ref(
            'notifications_settings_sale.email_sale_order_cancel')
        for order in self:
            website = order and order.website_id or None
            if website and order.website_id.notify_cancel:
                order.message_post_with_template(
                    template.id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res

    def action_done(self):
        res = super().action_done()
        template = self.env.ref(
            'notifications_settings_sale.email_sale_order_done')
        for order in self:
            website = order and order.website_id or None
            if website and order.website_id.notify_done:
                order.message_post_with_template(
                    template.id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res
