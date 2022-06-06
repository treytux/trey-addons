###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Owner',
    )
