###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    standard_price = fields.Float(
        string='Cost',
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    pl_discount = fields.Float(
        string='Pricelist Discount',
        digits=dp.get_precision('Pricelist Discount'),
        default=0.0,
    )

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        if not self.product_id:
            return res
        self.standard_price = (
            self.product_id and self.product_id.standard_price or 0)
        pl_discount = 0
        if self.product_id.lst_price != 0 and self.price_unit:
            pl_discount = (
                (self.product_id.lst_price - self.price_unit)
                / self.product_id.lst_price * 100)
        self.pl_discount = pl_discount
        return res
