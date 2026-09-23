###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockMoveLineRelation(models.Model):
    _name = 'stock.move.line.relation'
    _description = 'Stock move line relation'

    move_line_id = fields.Many2one(
        comodel_name='stock.move.line',
        string='Stock move line',
        readonly=True,
    )
    quantity = fields.Float(
        string='Quantity',
        readonly=True,
    )
    price_unit = fields.Float(
        string='Price unit',
        readonly=True,
    )
