###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_tax_curr = fields.Monetary(
        string='Total Tax',
        readonly=True,
        help='Sale Order Tax Amount in the company Currency',
        compute='_compute_amount_company',
        currency_field='company_currency_id',
        store=True,
    )
    amount_untaxed_curr = fields.Monetary(
        string='Total Untaxed',
        readonly=True,
        help='Sale Order Amount Untaxed in the company Currency',
        compute='_compute_amount_company',
        currency_field='company_currency_id',
        store=True,
    )

    @api.depends('amount_total', 'currency_rate', 'amount_tax',
                 'amount_untaxed')
    def _compute_amount_company(self):
        for order in self:
            if order.currency_id.id == order.company_id.currency_id.id:
                to_amount = order.amount_total
                to_tax = order.amount_tax
                to_untax = order.amount_untaxed
            else:
                to_amount = order.amount_total / order.currency_rate
                to_tax = order.amount_tax / order.currency_rate
                to_untax = order.amount_untaxed / order.currency_rate
            order.amount_total_curr = to_amount
            order.amount_tax_curr = to_tax
            order.amount_untaxed_curr = to_untax
