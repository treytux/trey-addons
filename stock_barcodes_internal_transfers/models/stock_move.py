###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _update_reserved_quantity(
            self, need, available_quantity, location_id, lot_id=None,
            package_id=None, owner_id=None, strict=True):
        self.ensure_one()
        if self.env.context.get('barcode_internal', False):
            lot_id = self.env['stock.production.lot'].search([
                ('name', '=', self.origin),
            ], limit=1)
            return super()._update_reserved_quantity(
                need=need, available_quantity=available_quantity,
                location_id=location_id, lot_id=lot_id, package_id=package_id,
                owner_id=owner_id, strict=strict)
        return super()._update_reserved_quantity(
            need=need, available_quantity=available_quantity,
            location_id=location_id, lot_id=lot_id, package_id=package_id,
            owner_id=owner_id, strict=strict)

    def _action_confirm(self, merge=True, merge_into=False):
        if self.picking_id and self.picking_id.picking_type_code == 'internal':
            merge = False
        return super()._action_confirm(merge=merge, merge_into=merge_into)
