###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_stock_info = fields.Selection(
        string='Product stock info',
        related='website_id.product_stock_info',
        readonly=False,
    )
    product_stock_location = fields.Selection(
        string='Product stock location',
        related='website_id.product_stock_location',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        product_stock_info = config_parameter.get_param(
            'website.product_stock_info')
        res.update(product_stock_info=product_stock_info)
        product_stock_location = config_parameter.get_param(
            'website.product_stock_location')
        res.update(product_stock_location=product_stock_location)
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.product_stock_info', self.product_stock_info)
        set_param('website.product_stock_location', self.product_stock_location)
