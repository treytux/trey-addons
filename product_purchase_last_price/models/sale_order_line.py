###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_last_price = fields.Float(
        string='Purchase last price',
        digits=dp.get_precision('Product Price'),
        compute='_compute_purchase_last_price',
        inverse='inverse_purchase_last_price',
        store=True,
    )

    def inverse_purchase_last_price(self):
        pass

    @api.depends('product_id')
    def _compute_purchase_last_price(self):
        for line in self:
            if not line.product_id or not line.product_id.purchase_last_price:
                continue
            line.purchase_last_price = line.product_id.purchase_last_price

    def set_purchase_last_price(self, purchase_last_price):
        for line in self:
            line.write({
                'purchase_last_price': purchase_last_price
            })

    def recalculate_purchase_last_price(self):
        for line in self:
            moves_done = line.move_ids.filtered(
                lambda move: move.state == 'done'
            )
            if not moves_done:
                continue
            move = moves_done.sorted('date')[-1]
            purchase_last_price = (
                line.product_id.calculate_purchase_last_price(move.date))
            line.set_purchase_last_price(purchase_last_price)
