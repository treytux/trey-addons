###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    margin_percent = fields.Float(
        string='Margin (%)',
        compute='_compute_margin_percent',
        store=True,
    )

    @api.depends('amount_untaxed', 'margin')
    @api.multi
    def _compute_margin_percent(self):
        for order in self:
            if not order.amount_untaxed:
                order.margin_percent = 0
                continue
            margin = (order.margin / order.amount_untaxed) * 100
            order.margin_percent = 0 if margin < 0 else margin
