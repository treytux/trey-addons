###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AcademyEvaluableConcept(models.Model):
    _name = 'academy.evaluable.concept'
    _description = 'Evaluable concept'

    name = fields.Char(
        string='Name',
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )
    show_in_bulletin = fields.Boolean(
        string='Show in bulletins',
        default=True,
    )
    activity_ids = fields.Many2many(
        comodel_name='academy.activity',
        relation='academy_activity2academy_evaluable_concept_rel',
        column1='evaluable_concept_id',
        column2='activity_id',
        string='Activities',
    )
    eval_concept_mark_ids = fields.Many2many(
        comodel_name='academy.evaluable.concept.mark',
        relation='academy_concept_mark2academy_evaluable_concept_rel',
        column1='evaluable_concept_id',
        column2='eval_concept_mark_id',
        string='Evaluable concept marks',
    )
