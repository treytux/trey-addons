###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    supplier_cost = fields.Float(
        string='Supplier cost',
        compute='_compute_product_supplier_cost',
        store=True,
    )

    @api.depends('seller_ids', 'seller_ids.price', 'seller_ids.sequence')
    def _compute_product_supplier_cost(self):
        for product in self:
            if not product.seller_ids:
                product.supplier_cost = 0
                continue
            sellers = product.seller_ids.sorted('sequence')
            seller_variants = sellers.filtered(
                lambda x: not x.product_id or x.product_id == product)
            if seller_variants:
                product.supplier_cost = seller_variants[0].price
                continue
            product.supplier_cost = sellers[0].price
