###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    warehouse_ids = fields.One2many(
        comodel_name='stock.warehouse',
        inverse_name='vehicle_id',
        string='Warehouses',
    )
