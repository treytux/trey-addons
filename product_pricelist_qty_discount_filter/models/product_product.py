###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_discount = fields.Boolean(
        string='Quantity discount',
        help='Indicates if the product has a discount for minimun quantity',
        compute='_compute_qty_discount',
        store=True,
    )

    @api.multi
    @api.depends('item_ids')
    def _compute_qty_discount(self):
        for product in self:
            product.qty_discount = False
            if any(item.min_quantity > 1 for item in product.item_ids):
                product.qty_discount = True
