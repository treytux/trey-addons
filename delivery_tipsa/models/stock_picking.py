###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tipsa_last_request = fields.Text(
        string='Last Tipsa request',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
    tipsa_last_response = fields.Text(
        string='Last Tipsa response',
        help='Used for issues debugging',
        copy=False,
        readonly=True,
    )
    tipsa_picking_reference = fields.Char(
        string='Picking number for Tipsa webservices',
        readonly=True,
        copy=False,
    )
