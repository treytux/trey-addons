###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError


class EduEnrollment(models.Model):
    _name = 'edu.enrollment'
    _description = 'Enrollment'
    _inherit = ['mail.thread']
    _rec_name = 'training_plan_id'

    name = fields.Char(
        string='Name',
        readonly=True,
        copy=False,
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
        copy=False,
    )
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
    )
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
        domain='[("training_plan_id", "=", training_plan_id)]',
        copy=False,
    )
    student_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Student',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
    )
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_enrollment2res_partner_rel',
        column1='enrollment_id',
        column2='partner_id',
        string='Tutors',
        domain='[("is_tutor", "=", True), ("student_ids", "in", student_id)]',
    )
    comments = fields.Text(
        string='Comments',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('ended', 'Ended'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    enrollment_line_ids = fields.One2many(
        comodel_name='edu.enrollment.line',
        inverse_name='enrollment_id',
        string='Enrollment Lines',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('classroom_id'):
                continue
            classroom = self.env['edu.training.plan.classroom'].browse(
                vals.get('classroom_id'))
            if classroom.student_limit <= classroom.number_students:
                raise UserError(_(
                    'Limit of students reached in classroom %s. '
                    'Please, select another classroom.') % classroom.name
                )
        res = super().create(vals_list)
        for enroll in res:
            if enroll:
                enroll.name = self.env[
                    'ir.sequence'].next_by_code('edu.enrollment')
        return res

    def to_active(self):
        self.ensure_one()
        if not self.state == 'draft':
            return
        if not self.classroom_id:
            raise UserError(_('Please, select a classroom.'))
        if (self.classroom_id.student_limit
                <= self.classroom_id.number_students):
            raise UserError(_(
                'Limit of students reached. Please, select another classroom.'))
        self.state = 'active'

    def to_ended(self):
        self.ensure_one()
        if not self.state == 'active':
            return
        self.state = 'ended'

    def to_cancelled(self):
        self.ensure_one()
        if self.state not in ['draft', 'active', 'ended']:
            return
        self.state = 'cancelled'

    def to_draft(self):
        self.ensure_one()
        if not self.state == 'cancelled':
            return
        self.state = 'draft'

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if not self.student_id:
            return
        self.tutor_ids = self.student_id.tutor_ids

    @api.onchange('training_plan_id')
    def _onchange_training_plan_id(self):
        self.enrollment_line_ids = False
        training_plan_id = self.training_plan_id
        if (not training_plan_id
                or not training_plan_id.typology_id
                or not training_plan_id.typology_id.enrollment_conditions):
            return
        self.comments = self.training_plan_id.typology_id.enrollment_conditions

    def fill_subjects(self):
        self.ensure_one()
        for subject in self.training_plan_id.subject_ids:
            if subject in self.enrollment_line_ids.mapped('subject_id'):
                continue
            self.env['edu.enrollment.line'].create({
                'enrollment_id': self.id,
                'subject_id': subject.id,
            })

    @api.constrains('classroom_id', 'student_id', 'state')
    def _check_unique(self):
        enrollments = self.search([
            ('classroom_id', '=', self.classroom_id.id),
            ('student_id', '=', self.student_id.id),
            ('state', '=', 'active'),
            ('id', '!=', self.id),
        ])
        if len(enrollments) >= 1:
            raise exceptions.ValidationError(
                _('There are duplicate active enrollments '
                  'for this student: %s') % self.student_id.name)
