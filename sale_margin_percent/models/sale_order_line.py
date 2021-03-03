###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    margin_percent = fields.Float(
        string='Margin (%)',
        compute='_compute_margin_percent',
        store=True,
    )

    @api.depends('margin', 'price_subtotal')
    @api.multi
    def _compute_margin_percent(self):
        for line in self:
            if not line.price_subtotal:
                line.margin_percent = 0
                continue
            margin = (line.margin / line.price_subtotal) * 100
            line.margin_percent = 0 if margin < 0 else margin
