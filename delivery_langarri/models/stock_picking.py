###############################################################################
# For copyright and license notices, see __manifest__.py file in root
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    langarri_last_request = fields.Text(
        string='Last request Langarri',
        copy=False,
        readonly=True,
    )
    langarri_last_response = fields.Text(
        string='Last response Langarri',
        copy=False,
        readonly=True,
    )
    tracking_number = fields.Char(
        string='Langarri tracking number',
        copy=False,
        readonly=True,
    )
    langarri_barcode = fields.Char(
        string='Barcode',
        copy=False,
        readonly=True,
    )
    langarri_package_barcodes = fields.Text(
        string='Package barcodes',
        copy=False,
        readonly=True,
    )

    def action_langarri_modify_shipping(self):
        self.ensure_one()
        return self.carrier_id.langarri_modify_shipping(self)
