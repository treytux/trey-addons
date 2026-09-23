###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    barcode = fields.Char(
        string='Barcode',
        copy=False,
        readonly=True,
    )
