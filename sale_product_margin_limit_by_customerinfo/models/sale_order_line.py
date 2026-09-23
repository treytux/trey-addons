###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_customerinfo_margin(self):
        self.ensure_one()
        if not self.product_id or not self.order_id.partner_id:
            return self.env['product.customerinfo']
        today = fields.Date.to_string(fields.Date.context_today(self))
        customerinfos = self.env['product.customerinfo'].search([
            ('name', '=', self.order_id.partner_id.id),
            ('min_qty', '<=', self.product_uom_qty),
            '|',
            ('product_id', '=', self.product_id.id),
            '&',
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('product_id', '=', False),
            '|',
            ('date_start', '=', False),
            ('date_start', '<=', today),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', today),
        ], order='product_id, sequence, min_qty desc, price')
        return customerinfos[:1]

    def _check_discount_limit(self):
        self.ensure_one()
        if not self.product_uom_qty * self.price_unit:
            self.amount_discount_approve = 0.0
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

    def _customerinfo_margin_price_limit(self, customerinfo):
        margin_limit = customerinfo.margin_limit
        if margin_limit >= 100:
            margin_limit = 99.99
        margin = margin_limit / 100.0
        return self.product_id.purchase_last_price / (1 - margin)

    def is_limit_ok(self):
        self.ensure_one()
        customerinfo = self._get_customerinfo_margin()
        if customerinfo:
            if not self._check_discount_limit():
                return False
            if self.env.user.ignore_margin_price_limit:
                return True
            price_unit = self.product_uom_qty and (
                self.price_subtotal / self.product_uom_qty) or 0.0
            margin_price_limit = self._customerinfo_margin_price_limit(
                customerinfo)
            if price_unit >= margin_price_limit:
                return True
            self.order_id.exception_limit_reason = _(
                'The product "%s" is selling below its minimum sale price '
                'unit %s for customer %s') % (
                    self.product_id.name, margin_price_limit,
                    self.order_id.partner_id.name)
            return False
        return super().is_limit_ok()
