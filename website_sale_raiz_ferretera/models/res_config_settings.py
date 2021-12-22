###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    raiz_ferretera_apikey = fields.Char(
        string='Raíz Ferretera API Key',
        related='website_id.raiz_ferretera_apikey',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        raiz_ferretera_apikey = config_parameter.get_param(
            'website.raiz_ferretera_apikey')
        res.update(raiz_ferretera_apikey=raiz_ferretera_apikey)
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.raiz_ferretera_apikey', self.raiz_ferretera_apikey)
