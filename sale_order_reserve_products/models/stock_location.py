###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    reserve_products_location = fields.Boolean(
        string='Location for product reservation',
        copy=False,
    )
