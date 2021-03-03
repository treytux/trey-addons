###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_advanced = fields.Float(
        string='Advanced',
        help='Total amount advanced without taxes',
        compute='_compute_advanced',
    )
    percent_advanced = fields.Float(
        string='Advanced (%)',
        compute='_compute_advanced',
    )

    @api.depends('order_line.is_downpayment', 'order_line', 'invoice_ids')
    def _compute_advanced(self):
        for sale in self:
            lines = sale.order_line.filtered(lambda l: l.is_downpayment)
            sale.amount_advanced = sum(lines.mapped('price_unit'))
            sale.percent_advanced = round(
                sale.amount_advanced * 100 / sale.amount_untaxed, 2)
