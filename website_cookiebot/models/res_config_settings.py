###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cookiebot_id = fields.Char(
        string='Cookiebot ID',
        related='website_id.cookiebot_id',
    )
    has_cookiebot_id = fields.Boolean(
        string='Cookiebot',
    )

    @api.onchange('has_cookiebot_id')
    def onchange_has_cookiebot_id(self):
        if not self.has_cookiebot_id:
            self.cookiebot_id = False

    @api.model
    def get_values(self):
        res = super().get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            has_cookiebot_id=get_param('website.has_cookiebot_id'),
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.has_cookiebot_id', self.has_cookiebot_id)
