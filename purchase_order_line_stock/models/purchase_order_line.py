# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    wh_qty_available = fields.Float(
        compute='_compute_wh_qty_available',
        string='Quantity on hand warehouse')
    wh_virtual_available = fields.Float(
        compute='_compute_wh_virtual_available',
        string='Forecast quantity warehouse')

    @api.one
    @api.depends(
        'product_id', 'order_id.picking_type_id',
        'order_id.picking_type_id.warehouse_id', 'product_id.qty_available')
    def _compute_wh_qty_available(self):
        if self.product_id.exists():
            warehouse_id = self.order_id.picking_type_id.warehouse_id.id
            product = self.env['product.product'].with_context(
                warehouse=warehouse_id).browse(self.product_id.id)
            self.wh_qty_available = product.qty_available

    @api.one
    @api.depends(
        'product_id', 'order_id.picking_type_id',
        'order_id.picking_type_id.warehouse_id',
        'product_id.virtual_available')
    def _compute_wh_virtual_available(self):
        if self.product_id.exists():
            warehouse_id = self.order_id.picking_type_id.warehouse_id.id
            product = self.env['product.product'].with_context(
                warehouse=warehouse_id).browse(self.product_id.id)
            self.wh_virtual_available = product.virtual_available
