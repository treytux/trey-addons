###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_confirmed_notify = fields.Boolean(
        string='State confirmed is notify',
    )
    is_assigned_notify = fields.Boolean(
        string='State assigned is notify',
    )

    @api.multi
    def action_assign(self):
        template_confirmed = self.env.ref(
            'notifications_settings_stock.email_stock_picking_confirmed')
        template_assigned = self.env.ref(
            'notifications_settings_stock.email_stock_picking_assigned')
        for picking in self:
            website = picking and picking.website_id or None
            confirmed = picking.is_confirmed_notify
            if (
                    not confirmed and picking.website_id.notify_stock_confirmed
                    and website):
                picking.is_confirmed_notify = True
                picking.message_post_with_template(
                    template_confirmed.id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
            res = super().action_assign()
            assigned = picking.is_assigned_notify
            state = picking.state
            if (
                    not assigned and state == 'assigned'
                    and picking.website_id.notify_stock_assigned and website):
                picking.is_assigned_notify = True
                picking.message_post_with_template(
                    template_assigned.id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res

    @api.multi
    def action_done(self):
        res = super().action_done()
        for picking in self:
            website = picking and picking.website_id or None
            state = picking.state
            if (
                    website and state == 'done'
                    and picking.website_id.notify_stock_done):
                template = self.env.ref(
                    'notifications_settings_stock.email_stock_picking_done')
                picking.message_post_with_template(
                    template.id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res

    @api.multi
    def action_cancel(self):
        res = super().action_cancel()
        for picking in self:
            website = picking and picking.website_id or None
            if website and picking.website_id.notify_stock_cancel:
                template = self.env.ref(
                    'notifications_settings_stock.email_stock_picking_cancel')
                picking.message_post_with_template(
                    template.id,
                    composition_mode='comment',
                    notif_layout='mail.mail_notification_light',
                )
        return res
