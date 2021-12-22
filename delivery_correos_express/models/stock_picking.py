###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    correos_express_last_request = fields.Text(
        string="Last Correos Express request",
        help="Used for issues debugging",
        copy=False,
        readonly=True,
    )
    correos_express_last_response = fields.Text(
        string="Last Correos Express response",
        help="Used for issues debugging",
        copy=False,
        readonly=True,
    )
