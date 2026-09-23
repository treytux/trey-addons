###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    standard_price = fields.Float(
        string='Cost',
        digits='Product Price',
    )
    pl_discount = fields.Float(
        string='Pricelist Discount',
        digits='Discount',
    )

    @api.onchange('product_id')
    def _onchange_product_id_simulator(self):
        if not self.product_id:
            self.standard_price = 0
            self.pl_discount = 0
            return
        self.standard_price = self.product_id.standard_price
        pl_discount = 0
        if self.product_id.lst_price != 0 and self.price_unit:
            pl_discount = (
                (self.product_id.lst_price - self.price_unit)
                / self.product_id.lst_price * 100)
        self.pl_discount = pl_discount
