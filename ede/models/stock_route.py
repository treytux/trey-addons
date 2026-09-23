###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockRoute(models.Model):
    _inherit = 'stock.route'

    is_ede = fields.Boolean(
        string='Is Ede',
        compute='_compute_is_ede',
    )
    is_ede_company = fields.Boolean(
        string='Ede Company',
    )
    is_ede_customer = fields.Boolean(
        string='Ede Customer',
    )

    @api.depends('is_ede_company', 'is_ede_customer')
    def _compute_is_ede(self):
        for route in self:
            route.is_ede = bool(
                route.is_ede_company or route.is_ede_customer)
