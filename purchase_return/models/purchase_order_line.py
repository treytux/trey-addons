###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _create_or_update_picking(self):
        if self.env.context.get('not_create_or_update_picking'):
            return
        return super()._create_or_update_picking()

    @api.multi
    def _prepare_stock_moves(self, picking):
        is_return = self.product_qty < 0
        self_not_update = self.with_context(not_create_or_update_picking=True)
        if is_return:
            self_not_update.product_qty *= -1
        res = super()._prepare_stock_moves(picking)
        if is_return:
            self_not_update.product_qty *= -1
            for item in res:
                if self.env.context.get('reverse_picking'):
                    item['picking_id'] = self.env.context['reverse_picking']
                item.update({
                    'to_refund': True,
                    'location_id': item['location_dest_id'],
                    'location_dest_id': item['location_id']})
        return res

    @api.multi
    def _create_stock_moves(self, picking):
        if any([l.product_qty < 0 for l in self]):
            reverse = picking.copy({
                'move_lines': [],
                'picking_type_id': (
                    picking.picking_type_id.return_picking_type_id.id or
                    picking.picking_type_id.id),
                'state': 'draft',
                'origin': _('Return of %s') % picking.origin,
                'location_id': picking.location_dest_id.id,
                'location_dest_id': picking.location_id.id})
            self = self.with_context(reverse_picking=reverse.id)
        return super()._create_stock_moves(picking)
