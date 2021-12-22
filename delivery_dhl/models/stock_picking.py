###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dhl_last_request = fields.Text(
        string='Last DHL request',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
    dhl_last_response = fields.Text(
        string='Last DHL response',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
    dhl_year = fields.Char(
        string='Year',
        help='Used to cancel a shipment',
    )
