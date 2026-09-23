###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    created_purchase_line_id = fields.Many2one(
        index=True,
    )
