###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class StockWarehouseOrderPoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    product_variant_count = fields.Integer(
        related='product_id.product_tmpl_id.product_variant_count')
    seller_ids = fields.One2many(
        related='product_id.product_tmpl_id.seller_ids')
    variant_seller_ids = fields.One2many(
        related='product_id.product_tmpl_id.variant_seller_ids')
