###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_sale_return = fields.Boolean(
        string='Is sale return',
        related='sale_id.is_return',
    )
