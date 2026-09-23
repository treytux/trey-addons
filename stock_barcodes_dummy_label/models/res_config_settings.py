###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    force_pallet_barcode = fields.Boolean(
        string='Force Pallet Barcode',
        help='Enable or disable the requirement for a pallet barcode on packages.',
        config_parameter='stock_barcodes_dummy_label.force_pallet_barcode',

    )

    @api.model
    def is_force_pallet_barcode_active(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'stock_barcodes_dummy_label.force_pallet_barcode')
        return param == 'True' if param else False
