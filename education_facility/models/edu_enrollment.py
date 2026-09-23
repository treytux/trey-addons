###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EduEnrollment(models.Model):
    _inherit = 'edu.enrollment'

    facility_id = fields.Many2one(
        comodel_name='edu.facility',
        string='Facility',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
        },
    )
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        domain="[('facility_id', '=', facility_id)]",
    )

    @api.onchange('facility_id')
    def onchange_facility_id(self):
        self.training_plan_id = False

    @api.onchange('training_plan_id')
    def onchange_training_plan_id(self):
        self.classroom_id = False
