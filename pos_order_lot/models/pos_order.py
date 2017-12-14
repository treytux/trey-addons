# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def create_picking(self):
        lots = []
        for line in self.lines:
            if line.product_id and line.product_id.type == 'service':
                continue
            lots.append({
                'name': line.name,
                'lot_id': line.lot_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uos': line.product_id.uom_id.id,
                'product_uos_qty': abs(line.qty),
                'product_uom_qty': abs(line.qty)})
        this = self.with_context(pos_order_lots=lots)
        return super(PosOrder, this).create_picking()
