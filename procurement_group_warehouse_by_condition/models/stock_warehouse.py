###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_warehouse_by_condition = fields.Boolean(
        string='Is warehouse by condition?',
    )

    def active_picking_types_by_warehouse(self):
        if not self.active:
            return False
        self.in_type_id.active = True
        self.out_type_id.active = True
        self.pick_type_id.active = self.delivery_steps != 'ship_only'
        self.pack_type_id.active = self.delivery_steps == 'pick_pack_ship'

    def inactive_picking_types_by_warehouse(self):
        if not self.active:
            return False
        picking_types = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.id),
        ])
        for picking_type in picking_types:
            picking_type.active = False

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'is_warehouse_by_condition' not in vals:
            return res
        for record in res:
            if record.is_warehouse_by_condition:
                record.inactive_picking_types_by_warehouse()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'is_warehouse_by_condition' not in vals:
            return res
        for record in self:
            if record.is_warehouse_by_condition:
                record.inactive_picking_types_by_warehouse()
            else:
                record.active_picking_types_by_warehouse()
        return res
