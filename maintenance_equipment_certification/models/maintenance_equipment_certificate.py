###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MaintenanceEquipmentCertificate(models.Model):
    _name = 'maintenance.equipment.certificate'
    _description = 'Maintenance equipment certificate'

    name = fields.Char()
    notes = fields.Text()
    certificate_file = fields.Binary(
        string='Certificate',
        attachment=True,
    )
    certificate_filename = fields.Char(
        string='Certificate file name',
    )
    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment',
    )
