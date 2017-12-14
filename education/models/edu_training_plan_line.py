# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class EduTrainingPlanLine(models.Model):
    _name = 'edu.training.plan.line'
    _description = 'Training plan line'
    _inherit = ['mail.thread']

    name = fields.Char(
        compute='_compute_name',
        string='Name',
        required=True)
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        ondelete='cascade',
        select=True,
        required=True)
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        required=True)
    teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Teacher',
        domain="[('is_teacher', '=', True)]")
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        help='Classrooms must be created from "Classroom" tab.')
    student_ids = fields.One2many(
        comodel_name='res.partner',
        compute='_compute_students',
        string='Students')

    @api.one
    @api.depends(
        'training_plan_id', 'subject_id', 'teacher_id', 'classroom_id')
    def _compute_name(self):
        data = dict(
            training_plan=self.training_plan_id.short_name or '',
            subject=self.subject_id.short_name or '',
            classroom=self.classroom_id and self.classroom_id.name or '',
            teacher=self.teacher_id and '(%s)' % self.teacher_id.name or '')
        self.name = (
            '%(training_plan)s %(subject)s %(classroom)s %(teacher)s' % data)

    @api.one
    def _compute_students(self):
        enroll_obj = self.env['edu.enrollment']
        enrollments = enroll_obj.search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', self.classroom_id.id),
            ('state', '=', 'active')])
        student_ids = [l.student_id.id for l in enrollments]
        self.student_ids = [(6, 0, student_ids)]
