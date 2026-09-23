###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AcademyEvaluableConceptMark(models.Model):
    _name = 'academy.evaluable.concept.mark'
    _description = 'Evaluable concept mark'

    name = fields.Char(
        string='Name',
        required=True,
    )
    evaluable_concept_ids = fields.Many2many(
        comodel_name='academy.evaluable.concept',
        relation='academy_concept_mark2academy_evaluable_concept_rel',
        column1='eval_concept_mark_id',
        column2='evaluable_concept_id',
        string='Evaluable concepts',
    )
