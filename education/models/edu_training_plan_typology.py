###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduTrainingPlanTypology(models.Model):
    _name = 'edu.training.plan.typology'
    _description = 'Training Plan Typology'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
    )
    enrollment_conditions = fields.Text(
        string='Enrollment Conditions',
    )
    access_requeriments = fields.Text(
        string='Access Requeriments',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
