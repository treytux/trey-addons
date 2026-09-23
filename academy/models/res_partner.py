###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import Command, _, api, exceptions, fields, models


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
        comodel_name='academy.enrollment',
        inverse_name='student_id',
        string='Enrollments',
    )
    academic_training_ids = fields.Many2many(
        comodel_name='academy.academic.training',
        relation='student_academic_training',
        column1='student_id',
        column2='academic_training_id',
        string='Academic training',
        domain='[("type", "!=", "teacher")]',
    )
    bulletins_count = fields.Integer(
        compute='_compute_bulletins_count',
        string='Marks bulletins Count',
    )
    students_enrollment_count = fields.Integer(
        compute='_compute_students_enrollment_count',
        string='Students enrollments',
    )
    related_employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Related work employee',
        groups='hr.group_hr_user',
        help='Related employee based on their work contact',
    )

    def _compute_bulletins_count(self):
        bulletin_obj = self.env['academy.marks.bulletin']
        for partner in self:
            partner.bulletins_count = bulletin_obj.search_count([
                ('name', '=', partner.id),
            ])

    def _compute_students_enrollment_count(self):
        for partner in self:
            if not partner.student_ids:
                partner.students_enrollment_count = 0
                continue
            enrollments_count = self.env['academy.enrollment'].search_count([
                ('tutor_ids', 'in', partner.id),
                ('student_id', 'in', partner.student_ids.ids),
            ])
            partner.students_enrollment_count = enrollments_count

    def show_partner_bulletins(self):
        self.ensure_one()
        bulletins = self.env['academy.marks.bulletin'].search([
            ('name', '=', self.id),
        ])
        action = self.env['ir.actions.act_window']._for_xml_id(
            'academy.action_academy_marks_bulletin')
        action['domain'] = [('id', 'in', bulletins.ids)]
        return action

    def show_students_enrollments(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'academy.action_academy_enrollment')
        enrollments = self.env['academy.enrollment'].search([
            ('tutor_ids', 'in', self.id),
            ('student_id', 'in', self.student_ids.ids),
        ])
        action['domain'] = [('id', 'in', enrollments.ids)]
        return action

    @api.onchange('vat')
    def _onchange_vat(self):
        self.vat = str(self.vat).upper() if self.vat else ''

    def create_user(self):
        self.ensure_one()
        group_ids = []
        if self.is_tutor:
            user = self.env.ref('academy.template_tutor_user')
        elif self.is_student:
            user = self.env.ref('academy.template_student_user')
        if user:
            group_ids = [g.id for g in user.groups_id]
        self.env['res.users'].create({
            'company_id': self.env.company.id,
            'name': self.name,
            'login': self.email or self.name,
            'password': self.email or self.name,
            'partner_id': self.id,
            'groups_id': [Command.set(group_ids)],
        })

    @api.constrains('academic_training_ids')
    def _check_student_academic_training(self):
        for student in self:
            if any(t.type == 'teacher' for t in student.academic_training_ids):
                raise exceptions.ValidationError(
                    _('The selected academic training is no compatible with '
                      'students.'))
