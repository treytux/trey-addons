###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    sequence = fields.Integer(
        string='Sequence',
        default=10)
