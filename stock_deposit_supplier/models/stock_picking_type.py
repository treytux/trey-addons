###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_supplier_deposit = fields.Boolean(
        string='Is supplier deposit?',
        help='If this field is marked, when the stock picking of "Deposit '
             'supplier" type that moves material from "Suppliers" to '
             '"Supplier warehouse" is created, another of the same type that '
             'goes from "Supplier warehouse" to "Stock" will be automatically '
             'created.',
        default=False,
    )
