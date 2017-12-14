# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class EduWizardEnrollStudent(models.TransientModel):
    _name = 'edu.wizard.enroll.student'
    _description = 'Wizard Enroll Student'

    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        default=lambda self: self.env.context.get('active_id'),
        required=True)
    total_student_classless = fields.Integer(
        string='Total Classless Students',
        help='Students enrolled in this training plan with no classroom.',
        compute='_compute_total_classless_students')
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        required=True,
        domain="[('training_plan_id','=',training_plan_id)]")
    total_student_class = fields.Integer(
        string='Total Students',
        help='Total students enrolled in this classroom.',
        compute='_compute_total_class_students')
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_wizard_enroll_student_res_partner_rel',
        column1='wiz_id',
        column2='student_id')
    student_enrolled_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_wizard_enroll_student_enrolled_res_partner_rel',
        column1='wiz_id',
        column2='student_id')

    @api.one
    @api.depends('training_plan_id')
    def _compute_total_classless_students(self):
        if not self.training_plan_id:
            return
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', None),
            ('state', '=', 'draft')])
        self.total_student_classless = len(enrollments)

    @api.one
    @api.depends('training_plan_id', 'classroom_id')
    def _compute_total_class_students(self):
        if not self.training_plan_id or not self.classroom_id:
            return
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', self.classroom_id.id)])
        self.total_student_class = len(enrollments)

    @api.multi
    def button_enroll(self):
        for student in self.student_ids:
            enrollments = self.env['edu.enrollment'].search([
                ('student_id', '=', student.id),
                ('training_plan_id', '=', self.training_plan_id.id),
                ('state', '=', 'draft')])
            for enroll in enrollments:
                enroll.classroom_id = self.classroom_id.id
                enroll.state = 'active'

    @api.onchange('training_plan_id')
    def _onchange_training_plan_id(self):
        if not self.training_plan_id:
            self.student_ids = None
            return
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', None),
            ('state', '=', 'draft')])
        self.student_enrolled_ids = None
        domain = {'domain': {'student_ids': [
            ('id', 'in', [e.student_id.id for e in enrollments])]}}
        return domain

    @api.onchange('classroom_id')
    def _onchange_classroom_id(self):
        if not self.classroom_id:
            self.student_enrolled_ids = None
            return
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', self.classroom_id.id)])
        self.student_enrolled_ids = [
            (6, 0, [e.student_id.id for e in enrollments])]
