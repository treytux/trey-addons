###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduTrainingPlan(models.Model):
    _inherit = 'edu.training.plan'

    facility_id = fields.Many2one(
        comodel_name='edu.facility',
        string='Facility',
    )
