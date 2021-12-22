###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nexmart_apikey = fields.Char(
        string='Nexmart API Key',
        related='website_id.nexmart_apikey',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        nexmart_apikey = config_parameter.get_param('website.nexmart_apikey')
        res.update(nexmart_apikey=nexmart_apikey)
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.nexmart_apikey', self.nexmart_apikey)
