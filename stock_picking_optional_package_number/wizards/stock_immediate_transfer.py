###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    package_number_required = fields.Boolean(
        string='Show package number in wizard',
        default=True,
    )

    @api.model
    def create(self, vals):
        if not vals.get('pick_ids', False):
            return super().create(vals)
        type_ids = []
        for picking_id in vals['pick_ids']:
            picking = self.env['stock.picking'].browse(picking_id[1])
            type_ids.append(picking.picking_type_id.id)
        if len(list(set(type_ids))) == 1:
            picking_type = self.env['stock.picking.type'].browse(type_ids[0])
            vals['package_number_required'] = (
                picking_type.package_number_required)
        elif len(list(set(type_ids))) > 1:
            picking_types = self.env['stock.picking.type'].browse(type_ids)
            if len(list(set(picking_types.mapped(
                    'package_number_required')))) == 1:
                vals['package_number_required'] = (
                    picking_types[0].package_number_required)
        return super().create(vals)
