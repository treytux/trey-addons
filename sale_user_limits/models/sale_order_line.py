###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    amount_discount_approve = fields.Float(
        string='Discount approve (%)',
        copy=False,
        readonly=True,
    )

    def check_approve(self):
        self.ensure_one()
        if not self.price_subtotal:
            self.amount_discount_approve = 0.
            return True
        total = self.price_unit * self.product_uom_qty
        discount = 100 - ((self.price_subtotal * 100) / total)
        if discount == self.amount_discount_approve:
            self.amount_discount_approve = discount
            return True
        if discount <= self.env.user.sales_discount_limit:
            self.amount_discount_approve = discount
            return True
        return False
