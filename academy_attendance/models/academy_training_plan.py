###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AcademyTrainingPlan(models.Model):
    _inherit = 'academy.training.plan'

    hr_holiday_ids = fields.Many2many(
        comodel_name='hr.holidays.public',
        relation='academy_training_plan2hr_holidays_public',
        column1='training_plan_id',
        column2='hr_holiday_id',
        string='Holidays calendar',
    )
