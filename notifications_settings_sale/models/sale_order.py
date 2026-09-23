###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    avoid_notifications = fields.Boolean(
        string='Avoid notifications',
        help='Avoid email notifications',
    )
    confirm_notified = fields.Boolean(
        string='Confirm notified',
    )

    def force_quotation_send(self):
        if ((not self.website_id or self.website_id.notify_quotation
                or self.state != 'draft') and not self.avoid_notifications):
            return super().force_quotation_send()
        self.write({
            'state': 'sent'
        })
        self.message_subscribe(self.partner_id.ids)
        return True

    def action_confirm(self):
        if not self.env.context.get('send_email', False):
            for order in self:
                if order.avoid_notifications or order.confirm_notified:
                    continue
                if order.website_id and order.website_id.notify_sale:
                    self = self.with_context(send_email=True)
        res = super().action_confirm()
        if res:
            self.filtered(lambda so: so.state == 'sale').write({
                'confirm_notified': True,
            })
        return res

    def action_cancel(self):
        res = super().action_cancel()
        if self.env.context.get('skip_mail_notification', False):
            return res
        template = self.env.ref(
            'notifications_settings_sale.email_sale_order_cancel')
        for order in self:
            if order.avoid_notifications:
                continue
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
            if order.avoid_notifications:
                continue
            website = order and order.website_id or None
            if website and order.website_id.notify_done:
                order.message_post_with_template(
                    template.id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res
