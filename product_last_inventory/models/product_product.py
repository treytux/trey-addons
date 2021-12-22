###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_inventory = fields.Datetime(
        string='Date of last inventory',
        compute='_compute_last_inventory_date',
        store=True,
        default=fields.Datetime.now,
    )

    @api.depends(
        'product_variant_ids',
        'product_variant_ids.stock_move_ids.product_qty',
        'product_variant_ids.stock_move_ids.state',
    )
    def _compute_last_inventory_date(self):
        stock_move_obj = self.env['stock.move']
        for product in self:
            move = stock_move_obj.search(
                [
                    ('product_id', '=', product.id),
                    ('inventory_id', '!=', False),
                ], limit=1)
            product.last_inventory = move.date
