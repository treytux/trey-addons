###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    purchase_last_price = fields.Float(
        string='Purchase last price',
        digits='Product Price',
        readonly=True,
        copy=False,
    )
    margin_purchase_last_price = fields.Float(
        string='Margin on purchase last price (%)',
        compute='_compute_margin_purchase_last_price',
    )

    @api.depends('purchase_last_price', 'list_price')
    def _compute_margin_purchase_last_price(self):
        for product in self:
            if not product.purchase_last_price or not product.list_price:
                product.margin_purchase_last_price = 0.0
                continue
            margin = product.purchase_last_price / product.list_price
            margin = round((margin - 1) * -100, 2)
            product.margin_purchase_last_price = margin >= 100 and 99.99 or margin

    def calculate_purchase_last_price(self, date_limit=False):
        for record in self:
            domain = [
                ('product_id', '=', record.id),
                ('state', '=', 'done'),
                ('picking_id.picking_type_code', '=', 'incoming'),
                ('purchase_line_id', '!=', False),
            ]
            if date_limit:
                domain.append(('date', '<=', date_limit))
            move = self.env['stock.move'].search(
                domain, order='date desc, id desc', limit=1)
            purchase_last_price = move.get_purchase_last_price()
            if not date_limit:
                record.purchase_last_price = purchase_last_price
            return purchase_last_price
