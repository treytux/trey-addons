###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

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
            if route.is_ede_company or route.is_ede_customer:
                route.is_ede = True

    @api.onchange('is_ede_company', 'is_ede_customer')
    def onchange_ede_customer_company(self):
        for route in self:
            if route.is_ede_company:
                route.is_ede_customer = False
            elif route.is_ede_customer:
                route.is_ede_company = False
