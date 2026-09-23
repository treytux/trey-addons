###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import Command, _, api, exceptions, fields, models


class AcademyEnrollment(models.Model):
    _name = 'academy.enrollment'
    _description = 'Enrollment'
    _inherit = ['mail.thread', 'utm.mixin']

    def _selection_enrollment_state(self):
        return [
            ('pending_level', _('Pending Level')),
            ('pending_group', _('Pending Group')),
            ('active', _('Attending')),
            ('ended', _('F.S.')),
            ('dropout', _('Drop Out')),
            ('cancelled', _('Cancelled')),
        ]

    name = fields.Char(
        string='Name',
        copy=False,
    )
    state = fields.Selection(
        selection=_selection_enrollment_state,
        string='State',
        default='pending_level',
        tracking=True,
    )
    training_plan_id = fields.Many2one(
        comodel_name='academy.training.plan',
        string='Training Plan',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'dropout': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        string='Activity',
        domain='[(\'training_plan_id\',\'=\',training_plan_id)]',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'dropout': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        required=True,
        copy=False,
    )
    student_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Student',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'dropout': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='academy_enrollment2res_partner_rel',
        column1='enrollment_id',
        column2='partner_id',
        string='Tutors',
        domain='[(\'is_tutor\', \'=\', True), (\'student_ids\','
        ' \'in\', student_id)]',
    )
    comments = fields.Text(
        string='Comments',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
        default=fields.Date.today(),
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'dropout': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    end_date = fields.Date(
        string='End date',
        required=True,
        default=fields.Date.today(),
        states={
            'ended': [('readonly', True)],
            'dropout': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    student_birthdate = fields.Date(
        related='student_id.birthdate_date',
        store=True,
    )
    partner_free_course = fields.Boolean(
        string='Free course',
        help='Free course only for this student',
    )
    reduced_price = fields.Boolean(
        string='Reduced price',
    )
    schedule_requested = fields.Char(
        string='Schedule requested',
    )
    title_action = fields.Char(
        string='Next action',
    )
    date_action = fields.Date(
        string='Next date action',
    )
    academic_training_ids = fields.Many2many(
        comodel_name='academy.academic.training',
        relation='enrollment_academic_training',
        column1='enrollment_id',
        column2='academic_training_id',
        string='Academic training',
        domain='[(\'type\', \'!=\', \'teacher\')]',
    )
    first_tutor_id = fields.Many2one(
        comodel_name='res.partner',
        string='First tutor',
        compute='_compute_first_tutor_id',
        store=True,
        readonly=True,
    )
    first_tutor_email = fields.Char(
        related='first_tutor_id.email',
        readonly=True,
    )
    first_tutor_mobile = fields.Char(
        related='first_tutor_id.mobile',
        readonly=True,
    )
    first_tutor_vat = fields.Char(
        related='first_tutor_id.vat',
        readonly=True,
    )
    end_reason = fields.Selection(
        selection=[
            ('dropout', 'Drop Out'),
            ('ended', 'F.S.'),
        ],
        string='End reason',
        tracking=True,
    )

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if not self.student_id:
            return
        self.tutor_ids = self.student_id.tutor_ids
        if not self.tutor_ids:
            self.tutor_ids = self.student_id.commercial_partner_id
        self.academic_training_ids = self.student_id.academic_training_ids

    @api.depends('tutor_ids')
    def _compute_first_tutor_id(self):
        for enrollment in self:
            if not enrollment.tutor_ids:
                enrollment.tutor_ids = \
                    enrollment.student_id.commercial_partner_id
            if enrollment.tutor_ids:
                enrollment.first_tutor_id = enrollment.tutor_ids[0]

    @api.model_create_multi
    def create(self, vals_list):
        check_student_limits = self.env.company.check_student_limits
        for vals in vals_list:
            activity = self.env['academy.activity'].browse(
                vals.get('activity_id'))
            if check_student_limits:
                activity._check_student_limit()
        res = super().create(vals_list)
        for enroll in res:
            enroll.name = self.env['ir.sequence'].next_by_code(
                'academy.enrollment')
            if len(enroll.academic_training_ids) > 0:
                enroll.student_id.write({
                    'academic_training_ids': [
                        Command.set(enroll.academic_training_ids.ids)],
                })
        return res

    def write(self, vals):
        state = vals.get('state', False)
        if self.env.company.check_student_limits and state == 'active':
            self.activity_id._check_student_limit()
        res = super().write(vals)
        academic_training_ids = vals.get('academic_training_ids', False)
        if not academic_training_ids or len(academic_training_ids[0][2]) == 0:
            return res
        for enroll in self:
            enroll.student_id.write({
                'academic_training_ids': vals['academic_training_ids'],
            })
        return res

    @api.onchange('training_plan_id')
    def _onchange_training_plan_id(self):
        self.activity_id = False
        if (
            not self.training_plan_id
            or not self.training_plan_id.typology_id
            or not self.training_plan_id.typology_id.enrollment_conditions
        ):
            self.comments = False
            return
        self.comments = self.training_plan_id.typology_id.enrollment_conditions

    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        if not self.activity_id:
            return
        self.start_date = self.activity_id.start_date
        self.end_date = self.activity_id.end_date

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        if self.env.context.get('skip_enrollment_checks'):
            return
        for enrollment in self:
            if (enrollment.start_date > enrollment.end_date):
                raise exceptions.ValidationError(
                    _('Start date must be equal or before than date end.'))
            if not enrollment.activity_id:
                return
            if (enrollment.start_date < enrollment.activity_id.start_date
                    or enrollment.end_date > enrollment.activity_id.end_date):
                raise exceptions.ValidationError(
                    _('The dates (%s) must be between %s and %s.') % (
                        enrollment.name, enrollment.activity_id.start_date,
                        enrollment.activity_id.end_date))

    @api.constrains('activity_id', 'student_id', 'state')
    def _check_unique(self):
        if self.env.context.get('skip_enrollment_checks'):
            return
        enrollments = self.search([
            ('activity_id', '=', self.activity_id.id),
            ('student_id', '=', self.student_id.id),
            ('id', '!=', self.id),
        ])
        if len(enrollments) >= 1:
            raise exceptions.ValidationError(
                _('There are duplicate active enrollments '
                  'for this student: %s.') % self.student_id.name)

    @api.constrains('training_plan_id', 'activity_id')
    def _check_training_plan_activity_relation(self):
        if not self.training_plan_id or not self.activity_id:
            return
        if self.activity_id.training_plan_id != self.training_plan_id:
            raise exceptions.ValidationError(
                _('The selected activity does not belong to the chosen '
                  'training plan.'))

    def _cron_check_enrollments_state(self):
        self = self.with_context(skip_enrollment_checks=True)
        plan_obj = self.env['academy.training.plan']
        activity_obj = self.env['academy.activity']
        plan_ids = plan_obj.close_active_training_plans()
        activity_ids = activity_obj.close_active_activities(plan_ids)
        self.finish_enrollments(activity_ids)

    def finish_enrollments(self, activity_ids=None):
        today = fields.Date.today()
        domain = [
            '&',
            ('state', 'in', ['pending_level', 'pending_group', 'active']),
            ('end_date', '<', today),
        ]
        if activity_ids:
            domain = ['|', ('activity_id', 'in', activity_ids.ids)] + domain
        enrollments_to_close = self.search(domain)
        for enrollment in enrollments_to_close:
            if enrollment.state in ['pending_level', 'pending_group']:
                enrollment.write({'state': 'cancelled'})
            elif enrollment.state == 'active' and enrollment.end_reason:
                enrollment.write({'state': enrollment.end_reason})
            elif enrollment.state == 'active':
                enrollment.write({'state': 'ended'})
            if enrollment.end_date > today:
                enrollment.end_date = today
