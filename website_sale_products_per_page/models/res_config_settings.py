###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ppg_values = fields.Char(
        string='Products per page',
        related='website_id.ppg_values',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        ppg = config_parameter.get_param('website.ppg_values')
        res.update(ppg_values=ppg)
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.ppg_values', self.ppg_values)
