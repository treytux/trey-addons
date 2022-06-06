###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    correos_last_request = fields.Text(
        string='Last Correos request',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
    correos_last_response = fields.Text(
        string='Last Correos response',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
