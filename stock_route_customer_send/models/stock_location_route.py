###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    is_customer_send = fields.Boolean(
        string='Is customer send?',
    )
