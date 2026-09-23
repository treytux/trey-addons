###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class AcademyAcademicTraining(models.Model):
    _name = 'academy.academic.training'
    _description = 'Academic Training'

    name = fields.Char(
        string='Name',
        required=True,
    )
    type = fields.Selection(
        selection=[
            ('student', 'For students'),
            ('teacher', 'For teachers'),
            ('both', 'For both'),
        ],
        string='Academic training type',
        required=True,
        default='student',
        help='Specifies whether this is for students, teachers, or both.',
    )

    @api.constrains('name', 'type')
    def _check_unique_name_and_type(self):
        for training in self:
            duplicate = self.search([
                ('name', '=', training.name),
                ('type', '=', training.type),
                ('id', '!=', training.id),
            ])
            if duplicate:
                raise exceptions.ValidationError(
                    _('The combination of Name and Academic Training Type '
                      'must be unique.'))
