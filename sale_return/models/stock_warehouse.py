###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    sale_return_default_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Sale return location',
        help='Default location that will be assigned on return sales order '
             'lines.\nIf left empty, the stock location of the warehouse '
             'selected in the sales order will be assigned.',
    )
