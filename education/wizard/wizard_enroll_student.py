###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EduWizardEnrollStudent(models.TransientModel):
    _name = 'edu.wizard.enroll.student'
    _description = 'Wizard Enroll Student'

    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        default=lambda self: self.env.context.get('active_id'),
        required=True,
    )
    total_student_classless = fields.Integer(
        string='Total Classless Students',
        help='Students in this training plan with no classroom or not '
        'enrolled.',
        compute='_compute_total_classless_students',
    )
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        required=True,
        domain='[("training_plan_id", "=", training_plan_id)]',
    )
    total_student_class = fields.Integer(
        string='Total Students',
        help='Total students enrolled in this classroom.',
        compute='_compute_total_class_students',
    )
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_wizard_enroll_student_res_partner_rel',
        column1='wiz_id',
        column2='student_id',
    )
    student_enrolled_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_wizard_enroll_student_enrolled_res_partner_rel',
        column1='wiz_id',
        column2='student_id',
    )

    @api.depends('training_plan_id', 'classroom_id')
    def _compute_total_classless_students(self):
        for enroll in self:
            if not enroll.training_plan_id:
                enroll.total_student_classless = False
                continue
            enrollments = self.env['edu.enrollment'].search([
                ('training_plan_id', '=', enroll.training_plan_id.id),
                ('state', '=', 'draft'),
                '|',
                ('classroom_id', '=', None),
                ('classroom_id', '=', enroll.classroom_id.id),
            ])
            enroll.total_student_classless = len(enrollments)

    @api.depends('training_plan_id', 'classroom_id')
    def _compute_total_class_students(self):
        for enroll in self:
            if not enroll.training_plan_id or not enroll.classroom_id:
                enroll.total_student_class = False
                continue
            enrollments = self.env['edu.enrollment'].search([
                ('training_plan_id', '=', enroll.training_plan_id.id),
                ('classroom_id', '=', enroll.classroom_id.id),
                ('state', '=', 'active'),
            ])
            enroll.total_student_class = len(enrollments)

    def button_enroll(self):
        self.ensure_one()
        for student in self.student_ids:
            enrollment = self.env['edu.enrollment'].search([
                ('student_id', '=', student.id),
                ('training_plan_id', '=', self.training_plan_id.id),
                ('state', '=', 'draft'),
            ], limit=1)
            if not enrollment:
                enrollment = self.env['edu.enrollment'].create({
                    'student_id': student.id,
                    'training_plan_id': self.training_plan_id.id,
                    'state': 'draft',
                })
            enrollment.classroom_id = self.classroom_id.id
            enrollment.fill_subjects()
            enrollment.to_active()

    @api.onchange('training_plan_id')
    def _onchange_training_plan_id(self):
        if not self.training_plan_id:
            self.student_ids = None
            return
        self.student_enrolled_ids = None

    @api.onchange('classroom_id')
    def _onchange_classroom_id(self):
        if not self.classroom_id:
            self.student_enrolled_ids = None
            return
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', self.classroom_id.id),
            ('state', '=', 'active'),
        ])
        self.student_enrolled_ids = [
            (6, 0, [e.student_id.id for e in enrollments])]
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('state', '=', 'draft'),
            '|',
            ('classroom_id', '=', self.classroom_id.id),
            ('classroom_id', '=', None),
        ])
        self.student_ids = [
            (6, 0, [e.student_id.id for e in enrollments])]
