###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AcademyEvaluation(models.Model):
    _name = 'academy.evaluation'
    _description = 'Evaluation'

    name = fields.Char(
        string='Name',
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    activity_ids = fields.Many2many(
        comodel_name='academy.activity',
        relation='academy_activity2academy_evaluation_rel',
        column1='evaluation_id',
        column2='activity_id',
        string='Activities',
    )
