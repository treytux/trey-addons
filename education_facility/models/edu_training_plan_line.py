###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduTrainingPlanLine(models.Model):
    _inherit = 'edu.training.plan.line'

    facility_id = fields.Many2one(
        comodel_name='edu.facility',
        string='Facility',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        domain="[('facility_id', '=', facility_id)]",
    )
