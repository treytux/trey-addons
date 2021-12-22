###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderType(models.Model):
    _inherit = 'sale.order.type'

    is_season = fields.Boolean(
        string='Is season',
    )
