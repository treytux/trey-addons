# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
import math


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_consume(self, product_qty, location_id=False,
                       restrict_lot_id=False, restrict_partner_id=False,
                       consumed_for=False):
        mrp_route = self.env.ref('mrp.route_warehouse0_manufacture')
        condition = (
            mrp_route not in self.product_id.route_ids or
            not restrict_lot_id or product_qty <= 1)
        if condition:
            return super(StockMove, self).action_consume(
                product_qty, location_id, restrict_lot_id, restrict_partner_id,
                consumed_for)

        def get_lot_name(name, count):
            return '%s-%s' % (name, str(count).zfill(6))

        quantity_rest = self.production_id.product_qty - product_qty
        if quantity_rest != 0:
            new_move_id = self.split(self, quantity_rest)
            new_move = self.env['stock.move'].browse(new_move_id)
            new_move.production_id = self.production_id.id
        new_moves = [self]
        self.product_uom_qty = product_qty < 1 and product_qty or 1
        restrict_lot = self.env['stock.production.lot'].browse(restrict_lot_id)
        lot_name = restrict_lot.name
        restrict_lot.name = get_lot_name(lot_name, 1)
        lot_dict = {self.id: restrict_lot.id}
        qty_rest = product_qty
        for i in range(2, int(math.ceil(product_qty)) + 1):
            qty_rest -= 1
            last_move = self.copy({
                'production_id': self.production_id.id,
                'raw_material_production_id': (
                    self.raw_material_production_id.id),
                'consumed_for': self.consumed_for.id,
                'product_uom_qty': qty_rest < 1 and qty_rest or 1})
            new_moves.append(last_move)
            new_lot = restrict_lot.copy({
                'name': get_lot_name(lot_name, i)})
            lot_dict[last_move.id] = new_lot.id
        res = []
        for new_move in new_moves:
            res.append(super(StockMove, new_move).action_consume(
                new_move.product_uom_qty, location_id, lot_dict[new_move.id],
                restrict_partner_id, consumed_for))
        return [r for r in res if r]
