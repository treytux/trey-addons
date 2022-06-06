###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    dummy_barcode = fields.Char(
        string='Dummy barcode',
    )
