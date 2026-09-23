###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    missing_taxes = fields.Boolean(
        compute='_compute_missing_taxes',
    )

    @api.depends('order_line.display_type', 'order_line.tax_id')
    def _compute_missing_taxes(self):
        for order in self:
            order.missing_taxes = False
            if not self.env.company.show_missing_taxes_in_so:
                continue
            lines = order.order_line.filtered(
                lambda o: o.display_type not in ('line_section', 'line_note'))
            if any(not line.tax_id for line in lines):
                order.missing_taxes = True
