###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notify_stock_confirmed = fields.Boolean(
        string='Notify stock confirmed',
        related='website_id.notify_stock_confirmed',
        readonly=False,
    )
    notify_stock_assigned = fields.Boolean(
        string='Notify stock assigned',
        related='website_id.notify_stock_assigned',
        readonly=False,
    )
    notify_stock_done = fields.Boolean(
        string='Notify stock done',
        related='website_id.notify_stock_done',
        readonly=False,
    )
    notify_stock_cancel = fields.Boolean(
        string='Notify stock cancel',
        related='website_id.notify_stock_cancel',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        confirm = config_parameter.get_param('website.notify_stock_confirmed')
        done = config_parameter.get_param('website.notify_stock_done')
        assigned = config_parameter.get_param('website.notify_stock_assigned')
        cancel = config_parameter.get_param('website.notify_stock_cancel')
        res.update(
            notify_stock_confirmed=confirm,
            notify_stock_assigned=assigned,
            notify_stock_done=done,
            notify_stock_cancel=cancel,
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.notify_stock_done', self.notify_stock_done)
        set_param('website.notify_stock_assigned', self.notify_stock_assigned)
        set_param('website.notify_stock_cancel', self.notify_stock_cancel)
        set_param(
            'website.notify_stock_confirmed',
            self.notify_stock_confirmed)
