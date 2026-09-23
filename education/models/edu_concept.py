###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduConcept(models.Model):
    _name = 'edu.concept'
    _description = 'Evaluable concept'

    name = fields.Char(
        string='Name',
        required=True,
    )
    value_type = fields.Selection(
        selection=[
            ('text', 'Text'),
            ('numeric', 'Numeric'),
        ],
        string='Value type',
        default='text',
        required=True,
    )
    values_valid = fields.Text(
        string='Valid values',
        help='Comma-separated list of valid values',
    )
    active = fields.Boolean(
        default=True,
    )
    subject_ids = fields.Many2many(
        comodel_name='edu.subject',
        relation='subject2edu_concept_rel',
        column1='concept_id',
        column2='subject_id',
        string='Subjects',
    )
