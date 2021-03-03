###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    allow_cancel_picking_relationed = fields.Boolean(
        string='Allow cancel picking relationated',
        help='When you check this option, you can cancel a stock picking '
             'related to another without canceling the latter.',
    )
