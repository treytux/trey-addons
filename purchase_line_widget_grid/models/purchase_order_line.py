# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_tmpl_id_purchase_order_variant_mgmt = fields.Many2one(
        comodel_name="product.template",
        related="product_id.product_tmpl_id")
    product_attribute_value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        related="product_id.attribute_value_ids")
