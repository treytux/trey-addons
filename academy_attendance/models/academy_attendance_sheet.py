###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo import api, fields, models


class AcademyAtendanceSheet(models.Model):
    _name = 'academy.attendance.sheet'
    _inherit = ['mail.thread']
    _description = 'Attendance Sheet'

    name = fields.Char(
        string='Name',
        default=lambda s: s.env['ir.sequence'].next_by_code(
            'academy.attendance.sheet'),
        readonly=True,
        copy=False,
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        readonly=True,
        tracking=True,
    )
    date_start = fields.Datetime(
        string='Start Date',
        readonly=True,
        copy=False,
    )
    date_end = fields.Datetime(
        string='End Date',
        readonly=True,
        copy=False,
    )
    duration = fields.Float(
        string='Duration',
        help='Class duration in minuts',
        compute='_compute_duration',
        store=True,
    )
    teacher_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Teacher',
        default=lambda self: self._get_teacher(),
        domain=[
            ('is_activity_selectable', '=', True),
        ],
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)],
        },
        required=True,
        tracking=True,
    )
    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        string='Activity',
        domain='[(\'teacher_id\',\'=\',teacher_id),'
        '(\'state\',\'=\',\'active\')]',
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)],
        },
        required=True,
        tracking=True,
    )
    user_id = fields.Many2one(
        related='activity_id.user_id',
    )
    substitution = fields.Boolean(
        string='Substitution?',
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)],
        },
    )
    substitute_teacher_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Substitute Teacher',
        domain=[('is_activity_selectable', '=', True)],
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)],
        },
        tracking=True,
    )
    attendance_line_ids = fields.One2many(
        comodel_name='academy.attendance.sheet.line',
        inverse_name='attendance_sheet_id',
        string='Attendance lines',
        states={
            'ended': [('readonly', True)],
        },
    )
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        compute='_compute_students',
        string='Students',
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('ready', 'Ready to Start'),
            ('ended', 'Ended'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
        tracking=True,
    )
    filters = fields.Selection(
        selection=[
            ('all', 'All Students'),
            ('manual', 'Manual Selection of Students'),
        ],
        string='Filter',
        default='all',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    attencance_sheet_line_id = fields.Many2one(
        comodel_name='academy.training.plan.attendance.line',
        string='Training plan sheet line',
        ondelete='cascade',
    )

    @api.model
    def _get_teacher(self):
        if not self.env.user.has_group('academy.group_academy_teacher'):
            return None
        return self.env.user.employee_id.id

    @api.onchange('teacher_id')
    def onchange_teacher_id(self):
        self.activity_id = []

    @api.depends('activity_id')
    def _compute_students(self):
        self.ensure_one()
        if not self.activity_id:
            self.student_ids = False
            return
        student_ids = []
        enrollments = self.env['academy.enrollment'].search([
            ('state', '=', 'active'),
            ('activity_id', '=', self.activity_id.id),
        ])
        student_ids = list(set([er.student_id.id for er in enrollments]))
        self.student_ids = [(6, 0, student_ids)]

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for record in self:
            if not record.date_start or not record.date_end:
                record.duration = 60
                continue
            delta = record.date_end - record.date_start
            record.duration = delta.total_seconds() / 60.0

    def to_ready_filter_all(self):
        self.ensure_one()
        enrollments = self.env['academy.enrollment'].search([
            ('state', '=', 'active'),
            ('activity_id', '=', self.activity_id.id),
        ])
        student_ids = list(set([er.student_id.id for er in enrollments]))
        self.attendance_line_ids = [
            (0, 0, {'student_id': e}) for e in student_ids]

    def to_ready(self):
        self.ensure_one()
        if not self.state == 'draft':
            return
        self.state = 'ready'
        if not hasattr(self, 'to_ready_filter_%s' % self.filters):
            return
        fnc = getattr(self, 'to_ready_filter_%s' % self.filters)
        fnc()

    def to_ended(self):
        self.ensure_one()
        if self.state != 'ready':
            return
        self.state = 'ended'
        self.date_end = fields.Datetime.now()

    def to_cancelled(self):
        self.ensure_one()
        if self.state not in ['draft', 'ready']:
            return
        self.state = 'cancelled'

    def to_draft(self):
        self.ensure_one()
        if self.state != 'cancelled':
            return
        self.state = 'draft'
        for line in self.attendance_line_ids:
            line.unlink()

    def _cron_set_academy_attendance_sheet_to_ready(self):
        today = datetime.today().replace(hour=0, minute=0, second=0)
        sheets = self.with_context(no_raise_teacher=True).search([
            ('state', '=', 'draft'),
            ('date_start', '>=', today),
            ('date_start', '<', today + timedelta(days=1)),
        ])
        for sheet in sheets:
            sheet.to_ready()
