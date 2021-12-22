###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_customer_code = fields.Char(
        related='move_id.product_customer_code',
        string='Product Customer Code',
    )
