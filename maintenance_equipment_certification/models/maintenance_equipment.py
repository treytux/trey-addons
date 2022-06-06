###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    certificate_ids = fields.One2many(
        comodel_name='maintenance.equipment.certificate',
        inverse_name='equipment_id',
    )
