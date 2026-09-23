###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alias_domain = fields.Char(
        related='company_id.alias_domain',
        string='Alias Domain',
        readonly=False
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.alias_domain = self.alias_domain

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            alias_domain=self.env.user.company_id.alias_domain,
        )
        return res
