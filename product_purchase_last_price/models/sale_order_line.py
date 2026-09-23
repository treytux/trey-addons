###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_last_price = fields.Float(
        string='Purchase last price',
        digits='Product Price',
        compute='_compute_purchase_last_price',
        inverse='_inverse_purchase_last_price',
        store=True,
    )

    @api.depends('product_id')
    def _compute_purchase_last_price(self):
        for line in self:
            line.purchase_last_price = line.product_id.purchase_last_price

    def _inverse_purchase_last_price(self):
        pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product = self.env['product.product'].browse(vals.get('product_id'))
            if product and 'purchase_last_price' not in vals:
                vals['purchase_last_price'] = product.purchase_last_price
        return super().create(vals_list)

    def set_purchase_last_price(self, purchase_last_price):
        for line in self:
            line.write({
                'purchase_last_price': purchase_last_price,
            })

    def recalculate_purchase_last_price(self):
        for line in self:
            moves_done = line.move_ids.filtered(
                lambda move: move.state == 'done')
            if not moves_done:
                continue
            move = moves_done.sorted('date')[-1]
            purchase_last_price = (
                line.product_id.calculate_purchase_last_price(move.date))
            line.set_purchase_last_price(purchase_last_price)
