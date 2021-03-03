###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cmr_code = fields.Integer(
        string='CMR Code',
        default=0,
        help="Code needed for CMR Report",
    )
