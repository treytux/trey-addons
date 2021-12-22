###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    is_season = fields.Boolean(
        string='Is season',
    )
