###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    log_import_template_product_variant = fields.Boolean(
        string='Enable save Logs of Product Variants Import',
        help='Enable or disable the saving of logs for product variants '
             'import operations.',
        config_parameter='import_template_product_variant.is_active',
    )

    @api.model
    def is_import_template_product_variant_logs_active(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'import_template_product_variant.is_active')
        return param == 'True' if param else False
