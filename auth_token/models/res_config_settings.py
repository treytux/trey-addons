###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    token_access = fields.Selection(
        string='Token access',
        related='website_id.token_access',
        readonly=False,
        help='Indicates which type of users can login with token',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter']
        token_access = param_obj.get_param('auth_token.token_access')
        res.update(token_access=token_access)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'auth_token.token_access', self.token_access or '')
