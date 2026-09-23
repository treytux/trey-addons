###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    certificate_number = fields.Char(
        string='Certificate number',
    )
