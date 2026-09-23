###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EduTrainingPlanClassroom(models.Model):
    _name = 'edu.training.plan.classroom'
    _description = 'Training plan classroom'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        ondelete='cascade',
        index=True,
        required=True,
    )
    course = fields.Char(
        string='Course',
        required=True,
    )
    group = fields.Char(
        string='Group',
        required=True,
    )
    student_ids = fields.One2many(
        comodel_name='res.partner',
        compute='_compute_students',
        string='Students',
    )
    student_limit = fields.Integer(
        string='Student limit',
        help='Number limit of students for that classrrom.',
        default=30,
    )
    number_students = fields.Integer(
        string='Number Students',
        compute='_compute_student_number',
    )

    def _compute_student_number(self):
        for classroom in self:
            classroom.number_students = len(classroom.student_ids)

    @api.constrains('training_plan_id', 'course', 'group')
    def _check_unique(self):
        for classroom in self:
            classrooms = self.search([
                ('training_plan_id', '=', classroom.training_plan_id.id),
                ('course', '=', classroom.course),
                ('group', '=', classroom.group),
            ])
            if ((len(classrooms) == 1 and classrooms.id != classroom.id)
                    or len(classrooms) > 1):
                raise ValidationError(
                    _("Classroom is repeated: %s") % classroom.name)

    @api.depends('course', 'group')
    def _compute_name(self):
        for classroom in self:
            classroom.name = ' '.join([
                classroom.course or '', classroom.group or ''])

    def _compute_students(self):
        enroll_obj = self.env['edu.enrollment']
        for classroom in self:
            enrollments = enroll_obj.search([
                ('training_plan_id', '=', classroom.training_plan_id.id),
                ('classroom_id', '=', classroom.id),
                ('state', '=', 'active'),
            ])
            student_ids = [enr.student_id.id for enr in enrollments]
            classroom.student_ids = [(6, 0, student_ids)]
