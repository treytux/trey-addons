###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    auto_return_picking = fields.Boolean(
        string='Create automatic return picking',
    )
