###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notify_sale = fields.Boolean(
        string='Notify sale',
        related='website_id.notify_sale',
        readonly=False,
    )
    notify_done = fields.Boolean(
        string='Notify blocked order',
        related='website_id.notify_done',
        readonly=False,
    )
    notify_cancel = fields.Boolean(
        string='Notify cancel',
        related='website_id.notify_cancel',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        sale = config_parameter.get_param('website.notify_sale')
        done = config_parameter.get_param('website.notify_done')
        cancel = config_parameter.get_param('website.notify_cancel')
        res.update(
            notify_sale=sale,
            notify_done=done,
            notify_cancel=cancel,
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.notify_sale', self.notify_sale)
        set_param('website.notify_done', self.notify_done)
        set_param('website.notify_cancel', self.notify_cancel)
