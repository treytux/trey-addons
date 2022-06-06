###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    package_number_required = fields.Boolean(
        string='Show package number in wizard',
        default=True,
    )
