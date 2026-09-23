###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    percent_probability = fields.Float(
        string='Probability %',
    )
    total_probability = fields.Float(
        string='Total probability',
        compute='_compute_total_probability',
        store=True,
    )

    @api.depends('amount_untaxed', 'percent_probability')
    def _compute_total_probability(self):
        for sale in self:
            sale.total_probability = sale.amount_untaxed * (
                sale.percent_probability / 100)
