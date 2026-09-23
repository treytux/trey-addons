###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_report_show_pack = fields.Boolean(
        related='company_id.sale_report_show_pack',
        string='Show pack lines in sale reports',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env['ir.config_parameter']
        sale_report_show_pack = param_obj.get_param(
            'print_formats_sale_product_pack.sale_report_show_pack')
        res.update(sale_report_show_pack=sale_report_show_pack)
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].set_param(
            'print_formats_sale_product_pack.sale_report_show_pack',
            self.sale_report_show_pack or True)
