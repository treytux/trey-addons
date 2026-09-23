###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduEvaluation(models.Model):
    _name = 'edu.evaluation'
    _description = 'Evaluation'

    name = fields.Char(
        string='Name',
    )
    sequence = fields.Integer(
        string='Sequence',
    )
