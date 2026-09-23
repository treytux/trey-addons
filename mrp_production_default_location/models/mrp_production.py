###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    location_src_id = fields.Many2one(
        compute='_compute_locations',
    )
    location_dest_id = fields.Many2one(
        compute='_compute_locations',
    )

    def _compute_locations(self):
        super()._compute_locations()
        for mrp in self:
            if mrp.company_id.mrp_location_src_id:
                mrp.location_src_id = mrp.company_id.mrp_location_src_id.id
            if mrp.company_id.mrp_location_dst_id:
                mrp.location_dest_id = mrp.company_id.mrp_location_dst_id.id

    def _compute_picking_type_id(self):
        super()._compute_picking_type_id()
        for mrp in self:
            if not mrp.company_id.mrp_location_src_id:
                continue
            warehouse = mrp.company_id.mrp_location_src_id.warehouse_id
            picking_type = self.env['stock.picking.type'].search([
                ('active', '=', 'True'),
                ('code', '=', 'mrp_operation'),
                ('warehouse_id.company_id', 'in', self.company_id.ids),
                ('warehouse_id', '=', warehouse.id),
            ], limit=1)
            mrp.picking_type_id = picking_type.id
