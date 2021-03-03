###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pixel_key = fields.Char(
        string='Pixel Key',
        related='website_id.pixel_key',
    )
    has_facebook_pixel = fields.Boolean(
        string="Facebook Pixel",
    )

    @api.onchange('has_facebook_pixel')
    def onchange_has_facebook_pixel(self):
        if not self.has_facebook_pixel:
            self.pixel_key = False

    @api.model
    def get_values(self):
        res = super().get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            has_facebook_pixel=get_param('website.has_facebook_pixel'),
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.has_facebook_pixel', self.has_facebook_pixel)
