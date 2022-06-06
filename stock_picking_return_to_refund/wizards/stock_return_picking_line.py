###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    to_refund = fields.Boolean(
        default=True,
    )
