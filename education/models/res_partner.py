###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(
        string='Student',
    )
    is_teacher = fields.Boolean(
        string='Teacher',
    )
    is_tutor = fields.Boolean(
        string='Tutor',
    )
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='student_tutor_rel',
        column1='student_id',
        column2='tutor_id',
        string='Tutors',
    )
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='student_tutor_rel',
        column1='tutor_id',
        column2='student_id',
        string='Students',
    )
    enrollment_ids = fields.One2many(
        comodel_name='edu.enrollment',
        inverse_name='student_id',
        string='Enrollments',
    )
    classroom_ids = fields.Many2many(
        comodel_name='edu.training.plan.classroom',
        relation='student_classroom_rel',
        column1='student_id',
        column2='classroom_id',
        compute='_compute_classrooms_ids',
        string='Classrooms',
        store=True,
    )
    academic_training_ids = fields.Many2many(
        comodel_name='edu.academic.training',
        relation='student_academic_training',
        column1='student_id',
        column2='academic_training_id',
        string='Academic Training',
    )
    campus_user = fields.Char(
        string='Campus User',
    )
    campus_password = fields.Char(
        string='Campus Password',
    )
    bulletins_count = fields.Integer(
        compute='_compute_bulletins_count',
        string='Marks bulletins Count',
    )

    def create_user(self):
        self.ensure_one()
        group_ids = []
        if self.is_student:
            user = self.env.ref('education.template_student_user')
        elif self.is_teacher:
            user = self.env.ref('education.template_teacher_user')
        elif self.is_tutor:
            user = self.env.ref('education.template_tutor_user')
        if user:
            group_ids = [g.id for g in user.groups_id]
        user_vals = {
            'company_id': self.company_id.id,
            'name': self.name,
            'login': self.email or self.name,
            'password': self.email or self.name,
            'partner_id': self.id,
            'groups_id': [(6, 0, group_ids)],
        }
        self.env['res.users'].create(user_vals)

    @api.depends('enrollment_ids', 'enrollment_ids.state')
    def _compute_classrooms_ids(self):
        enroll_obj = self.env['edu.enrollment']
        for partner in self:
            if not partner.is_student:
                continue
            enrollment_ids = enroll_obj.search([
                ('student_id', '=', partner.id),
                ('state', '=', 'active'),
            ])
            if not enrollment_ids:
                continue
            partner.classroom_ids = [
                (6, 0, [e.classroom_id.id for e in enrollment_ids])]

    def _compute_bulletins_count(self):
        edu_marks_bulletin_obj = self.env['edu.marks.bulletin']
        for partner in self:
            partner.bulletins_count = edu_marks_bulletin_obj.search_count([
                ('name', '=', partner.id),
            ])

    def show_partner_bulletins(self):
        self.ensure_one()
        bulletins = self.env['edu.marks.bulletin'].search([
            ('name', '=', self.id),
        ])
        action = self.env.ref('education.action_edu_marks_bulletin').read()[0]
        action['domain'] = [('id', 'in', bulletins.ids)]
        return action
