###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class AcademyActivity(models.Model):
    _name = 'academy.activity'
    _description = 'Activity'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        required=True,
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
        tracking=True,
    )
    invoice_tutors = fields.Boolean(
        string='Invoice tutors',
        help='If checked, the tutors will be invoiced.',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
    )
    activity_price_reduced = fields.Monetary(
        string='Activity price reduced',
        currency_field='currency_id',
    )
    activity_price = fields.Monetary(
        string='Activity price',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    training_plan_id = fields.Many2one(
        comodel_name='academy.training.plan',
        string='Training Plan',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        ondelete='cascade',
        index=True,
        required=True,
    )
    enrollment_ids = fields.One2many(
        comodel_name='academy.enrollment',
        inverse_name='activity_id',
        string='Enrollments',
    )
    enrollment_count = fields.Integer(
        compute='_compute_enrollments',
        string='Enrollments count',
    )
    invoice_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='activity_id',
        string='Invoices',
    )
    invoice_count = fields.Integer(
        compute='_compute_invoices',
        string='Invoices count',
    )
    evaluation_ids = fields.Many2many(
        comodel_name='academy.evaluation',
        relation='academy_activity2academy_evaluation_rel',
        column1='activity_id',
        column2='evaluation_id',
        string='Evaluations',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    evaluable_concept_ids = fields.Many2many(
        comodel_name='academy.evaluable.concept',
        relation='academy_activity2academy_evaluable_concept_rel',
        column1='activity_id',
        column2='evaluable_concept_id',
        string='Evaluable concepts',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    teacher_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Teacher',
        domain=[('is_activity_selectable', '=', True)],
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    gross_salary = fields.Float(
        string='Gross salary',
    )
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        compute='_compute_students',
        string='Students',
        store=True,
    )
    student_limit = fields.Integer(
        string='Student limit',
        help='Number limit of students for that activity.',
        default=30,
    )
    student_count = fields.Integer(
        compute='_compute_students',
        string='Enrolled students',
        store=True,
    )
    active_count = fields.Integer(
        compute='_compute_students',
        string='Attending',
        store=True,
    )
    ended_count = fields.Integer(
        compute='_compute_students',
        string='F.S',
        store=True,
    )
    dropout_count = fields.Integer(
        compute='_compute_students',
        string='Dropout',
        store=True,
    )
    pending_level_count = fields.Integer(
        compute='_compute_students',
        string='Pending level',
        store=True,
    )
    pending_group_count = fields.Integer(
        compute='_compute_students',
        string='Pending group',
        store=True,
    )
    cancelled_count = fields.Integer(
        compute='_compute_students',
        string='Cancelled',
        store=True,
    )
    bulletin_ids = fields.One2many(
        comodel_name='academy.marks.bulletin',
        inverse_name='activity_id',
        string='Bulletins',
    )
    bulletin_count = fields.Integer(
        compute='_compute_bulletins',
        string='Bulletins count',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        domain=[('share', '=', False)],
        required=True,
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    end_date = fields.Date(
        string='End date',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
    )
    schedule = fields.Char(
        string='Schedule',
    )
    estimated_hours = fields.Float(
        string='Estimated hours',
    )
    notes = fields.Text()

    @api.onchange('training_plan_id')
    def _onchange_training_plan_id(self):
        if not self.training_plan_id:
            return
        self.user_id = self.training_plan_id.user_id
        self.start_date = self.training_plan_id.start_date
        self.end_date = self.training_plan_id.end_date

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for activity in self:
            if (activity.start_date > activity.end_date):
                raise exceptions.ValidationError(
                    _('Start date must be equal or before than date end.'))
            if not activity.training_plan_id:
                return
            if (activity.start_date < activity.training_plan_id.start_date
                    or activity.end_date > activity.training_plan_id.end_date):
                raise exceptions.ValidationError(
                    _('The dates of the activity (%s) must be compatible with '
                      'the dates of the training plan.' % activity.name))
            if not activity.enrollment_ids:
                continue
            activity.enrollment_ids._check_dates()

    @api.depends('enrollment_ids.state')
    def _compute_students(self):
        for activity in self:
            enrollments = activity.enrollment_ids
            student_ids = [
                enr.student_id.id for enr in enrollments.filtered(
                    lambda e: e.state in ['active', 'ended', 'dropout'])]
            activity.student_ids = [(6, 0, student_ids)]
            activity.student_count = len(student_ids)
            activity.active_count = len(
                enrollments.filtered(lambda e: e.state == 'active'))
            activity.ended_count = len(
                enrollments.filtered(lambda e: e.state == 'ended'))
            activity.dropout_count = len(
                enrollments.filtered(lambda e: e.state == 'dropout'))
            activity.cancelled_count = len(
                enrollments.filtered(lambda e: e.state == 'cancelled'))
            activity.pending_group_count = len(
                enrollments.filtered(lambda e: e.state == 'pending_group'))
            activity.pending_level_count = len(
                enrollments.filtered(lambda e: e.state == 'pending_level'))

    def _compute_invoices(self):
        for line in self:
            line.invoice_count = len(line.invoice_ids)

    def _compute_bulletins(self):
        for line in self:
            line.bulletin_count = len(line.bulletin_ids)

    def _check_student_limit(self):
        for activity in self:
            if activity.student_limit <= activity.student_count:
                raise exceptions.UserError(_(
                    'Limit of students reached in activity %s. '
                    'Please, select another activity.') % activity.name)

    def _compute_enrollments(self):
        for line in self:
            line.enrollment_count = len(line.enrollment_ids)

    def close_active_activities(self, plan_ids=None):
        today = fields.Date.today()
        domain = [
            '&',
            ('state', 'in', ['draft', 'active']),
            ('end_date', '<', today),
        ]
        if plan_ids:
            domain = ['|', ('training_plan_id', 'in', plan_ids.ids)] + domain
        activities_to_close = self.search(domain)
        if activities_to_close:
            activities_to_close.write({'state': 'ended'})
            activities_future_end_date = activities_to_close.filtered(
                lambda a: a.end_date > today)
            if activities_future_end_date:
                activities_future_end_date.write({'end_date': today})
        return activities_to_close

    def to_active(self):
        self.ensure_one()
        if not self.state == 'draft':
            return
        self.state = 'active'

    def to_ended(self):
        self.ensure_one()
        if not self.state == 'active':
            return
        if self.enrollment_ids:
            self.enrollment_ids.finish_enrollments(self)
        self.state = 'ended'
        self.end_date = fields.Date.today()

    def to_cancelled(self):
        self.ensure_one()
        if self.state not in ['draft', 'active']:
            return
        self.state = 'cancelled'

    def to_draft(self):
        self.ensure_one()
        if not self.state == 'cancelled':
            return
        self.state = 'draft'

    def button_show_enrolled_students(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'academy.action_academy_res_partner_student_admin')
        action['domain'] = [('id', 'in', self.student_ids.ids)]
        return action

    def button_open_marks_bulletin(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'academy.action_academy_marks_bulletin')
        action['domain'] = [('id', 'in', self.bulletin_ids.ids)]
        return action

    def button_show_activity_invoices(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_move_out_invoice_type')
        action['domain'] = [('id', 'in', self.invoice_ids.ids)]
        return action

    def button_open_enrollment(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'academy.action_academy_enrollment')
        action['domain'] = [('id', 'in', self.enrollment_ids.ids)]
        return action

    def button_invoice_period(self):
        # To-Do: implement this method
        return True
