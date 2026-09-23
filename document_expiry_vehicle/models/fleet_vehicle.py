###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    expiry_docs_ids = fields.One2many(
        comodel_name='document.expiry',
        inverse_name='vehicle_id',
        string='Documentation',
    )
    expiry_docs_count = fields.Integer(
        compute='_compute_expiry_docs_count',
        string='Documentation Count',
    )

    @api.multi
    def _compute_expiry_docs_count(self):
        for vehicle in self:
            vehicle.expiry_docs_ids_count = len(vehicle.expiry_docs_ids)

    @api.multi
    def action_view_expiry_docs(self):
        self.ensure_one()
        action = self.env.ref(
            'document_expiry_vehicle.action_vehicle_document_expiry').read()[0]
        action['domain'] = [('vehicle_id', '=', self.id)]
        action['context'] = {
            'default_vehicle_id': self.id,
            'default_owner_type': 'vehicle',
        }
        return action
