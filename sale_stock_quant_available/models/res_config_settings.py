###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_stock_popover = fields.Boolean(
        string='Make window popup',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            sale_stock_popover=get_param(
                'sale_stock_quant_available.sale_stock_popover',
                'False').lower() == 'true',
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('sale_stock_quant_available.sale_stock_popover',
                  repr(self.sale_stock_popover))
