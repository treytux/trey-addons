###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    portal_access_scope = fields.Selection(
        string='Portal access',
        related='website_id.portal_access_scope',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        portal_access_scope = config_parameter.get_param(
            'website.portal_access_scope')
        res.update(portal_access_scope=portal_access_scope)
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.portal_access_scope', self.portal_access_scope)
