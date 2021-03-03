###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    amount_discount_approve = fields.Float(
        string='Discount approve (%)',
        copy=False,
        readonly=True,
    )

    def is_limit_ok(self):
        self.ensure_one()
        if not self.product_uom_qty * self.price_unit:
            self.amount_discount_approve = 0.
            return True
        if self.discount == self.amount_discount_approve:
            self.amount_discount_approve = self.discount
            return True
        if self.discount <= self.env.user.sales_discount_limit:
            self.amount_discount_approve = self.discount
            return True
        self.order_id.exception_limit_reason = _(
            'A discount line is upper that your limit %s%%, your manager '
            'need to approve this operation') % (
                self.env.user.sales_discount_limit)
        return False
