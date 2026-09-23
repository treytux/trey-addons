###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(
            self, product_id=None, line_id=None, add_qty=0, set_qty=0,
            **kwargs):
        self.ensure_one()
        res = super()._cart_update(
            product_id, line_id, add_qty, set_qty, **kwargs)
        order_line = self.env['sale.order.line'].browse(res.get('line_id'))
        if not order_line or not order_line.product_id:
            return res
        partner_id = self.partner_id.commercial_partner_id
        product_tmpl = order_line.product_id.product_tmpl_id
        quantity = order_line.product_uom_qty
        customerinfo = self.env['product.template'].get_product_customerinfo(
            product_tmpl.id, quantity, partner_id, order_line.product_id.id)
        if customerinfo:
            price = customerinfo.currency_id._convert(
                customerinfo.price, self.currency_id, self.company_id,
                fields.Date.context_today(self), round=False)
            order_line.discount = customerinfo.discount
            order_line.price_unit = price
        return res
