# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class EduTrainingPlanClassroom(models.Model):
    _name = 'edu.training.plan.classroom'
    _description = 'Training plan classroom'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True)
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        ondelete='cascade',
        select=True,
        required=True)
    course = fields.Char(
        string='Course',
        required=True)
    group = fields.Char(
        string='Group',
        required=True)
    student_ids = fields.One2many(
        comodel_name='res.partner',
        compute='_compute_students',
        string='Students')
    student_limit = fields.Integer(
        string='Student limit',
        help='Number limit of students for that classrrom.',
        default=30)
    number_students = fields.Integer(
        string='Number Students',
        compute='_get_student_number')

    @api.one
    def _get_student_number(self):
        self.number_students = len(self.student_ids)

    @api.constrains('training_plan_id', 'course', 'group')
    def _check_unique(self):
        classrooms = self.search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('course', '=', self.course),
            ('group', '=', self.group)])
        if ((len(classrooms) == 1 and classrooms.id != self.id) or
                len(classrooms) > 1):
            raise ValidationError(_("Classroom is repeated: %s") % self.name)

    @api.one
    @api.depends('course', 'group')
    def _compute_name(self):
        self.name = ' '.join([self.course or '', self.group or ''])

    @api.one
    def _compute_students(self):
        enroll_obj = self.env['edu.enrollment']
        enrollments = enroll_obj.search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', self.id),
            ('state', '=', 'active')])
        student_ids = [l.student_id.id for l in enrollments]
        self.student_ids = [(6, 0, student_ids)]
