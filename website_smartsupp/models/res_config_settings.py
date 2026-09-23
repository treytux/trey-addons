###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    smartsupp_key = fields.Char(
        string='Installation Code',
        related='website_id.smartsupp_key',
        readonly=False,
    )
    has_smartsupp_key = fields.Boolean(
        string='Smartsupp',
    )

    @api.onchange('has_smartsupp_key')
    def onchange_has_smartsupp_key(self):
        if not self.has_smartsupp_key:
            self.smartsupp_key = False

    @api.model
    def get_values(self):
        res = super().get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            has_smartsupp_key=get_param('website.has_smartsupp_key'),
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.has_smartsupp_key', self.has_smartsupp_key)
