###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    qc_test_ids = fields.Many2many(
        string='Quality Control Tests',
        comodel_name='qc.test',
    )
