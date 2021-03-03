###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_price_unit = fields.Float(
        string='Sale price unit',
        digits=dp.get_precision('Product Price'),
        compute='_compute_sale_price',
        store=True,
    )
    sale_discount = fields.Float(
        string='Sale discount',
        digits=dp.get_precision('Discount'),
        compute='_compute_sale_price',
        store=True,
    )
    sale_subtotal = fields.Float(
        string='Sale subtotal',
        compute='_compute_sale_price',
        store=True,
    )
    purchase_price_unit = fields.Float(
        string='Purchase price unit',
        digits=dp.get_precision('Product Price'),
        compute='_compute_purchase_price',
        store=True,
    )
    purchase_discount = fields.Float(
        string='Purchase discount',
        digits=dp.get_precision('Discount'),
        compute='_compute_purchase_price',
        store=True,
    )
    purchase_subtotal = fields.Float(
        string='Purchase subtotal',
        compute='_compute_purchase_price',
        store=True,
    )

    @api.depends('sale_line_id')
    def _compute_sale_price(self):
        for move in self:
            line = move.sale_line_id
            if not line:
                move.sale_price_unit = 0
                move.sale_discount = 0
                move.sale_subtotal = 0
                continue
            move.sale_price_unit = line.price_unit
            move.sale_discount = line.discount
            move.sale_subtotal = line.price_subtotal

    @api.depends('purchase_line_id')
    def _compute_purchase_price(self):
        for move in self:
            line = move.purchase_line_id
            if not line:
                move.purchase_price_unit = 0
                move.purchase_discount = 0
                move.purchase_subtotal = 0
                continue
            move.purchase_price_unit = line.price_unit
            move.purchase_discount = line.discount
            move.purchase_subtotal = line.price_subtotal
