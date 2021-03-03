###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    limit_orders_quotations = fields.Integer(
        string='Maximum number of sale orders and quotations to show',
        related='website_id.limit_orders_quotations',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env['ir.config_parameter'].sudo()
        limit = int(config.get_param('website.limit_orders_quotations'))
        res.update(limit_orders_quotations=limit)
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param(
            'website.limit_orders_quotations', self.limit_orders_quotations)
