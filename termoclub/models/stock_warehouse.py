###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    termoclub_address_id = fields.Integer(
        string='TermoClub address ID',
        required=True,
        default=1,
    )
