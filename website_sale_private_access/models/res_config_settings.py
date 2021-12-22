###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_private_shop = fields.Boolean(
        string='Is private shop',
        related='website_id.is_private_shop',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        private = config_parameter.get_param('website.is_private_shop')
        res.update(is_private_shop=private)
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.is_private_shop', self.is_private_shop)
