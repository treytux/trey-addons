###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    qc_test_ids = fields.Many2many(
        string='Quality Control Tests',
        comodel_name='qc.test',
    )

    @api.onchange('category_id')
    def _onchange_category_id(self):
        res = super()._onchange_category_id()
        self.qc_test_ids = self.category_id.qc_test_ids
        return res
