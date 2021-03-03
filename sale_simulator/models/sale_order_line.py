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

    @api.onchange('product_id')
    def product_id_change(self):
        self.standard_price = (
            self.product_id and self.product_id.standard_price or 0)
        return super().product_id_change()
