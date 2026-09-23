###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockLocation(models.Model):
    _name = 'stock.location'
    _inherit = ['stock.location', 'website.published.mixin']

    is_published = fields.Boolean(
        default=True,
    )
