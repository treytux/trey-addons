###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    ede_document_id = fields.Char(
        string='Ede document',
    )
