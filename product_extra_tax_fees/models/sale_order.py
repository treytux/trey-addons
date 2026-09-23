###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tax_fee_amount = fields.Float(
        string='Tax fee amount',
        compute='_compute_tax_fee_amount',
    )

    def _compute_tax_fee_amount(self):
        for sale in self:
            sale.tax_fee_amount = sum(
                sale.mapped('order_line.tax_fee_ids').filtered(
                    lambda tax_ln: tax_ln.tax_fee_id.show_on_invoice
                    in ['value', 'always'] and tax_ln.tax_fee_amount).mapped(
                    'tax_fee_amount'))
