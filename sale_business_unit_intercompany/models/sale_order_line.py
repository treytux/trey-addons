###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def invoice_line_create_vals(self, invoice_id, qty):
        user_company = self.env.user.company_id
        company = (
            self.product_id.unit_id and self.product_id.unit_id.company_id)
        if company:
            self.env.user.company_id = company.id
        res = super().invoice_line_create_vals(invoice_id, qty)
        if company:
            self.env.user.company_id = user_company
        return res
