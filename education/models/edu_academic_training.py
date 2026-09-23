###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduAcademicTraining(models.Model):
    _name = 'edu.academic.training'
    _description = 'Academic Training'

    name = fields.Char(
        string='Name',
        required=True,
    )
