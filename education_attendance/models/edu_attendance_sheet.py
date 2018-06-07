# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class EduAtendanceSheet(models.Model):
    _name = 'edu.attendance.sheet'
    _inherit = ['mail.thread']
    _description = 'Attendance Sheet'

    name = fields.Char(
        string='Name',
        default=lambda s: s.env['ir.sequence'].get('edu.attendance.sheet'),
        readonly=True,
        copy=False)
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)]},
        track_visibility='onchange')
    date_start = fields.Datetime(
        string='Start Date',
        readonly=True,
        copy=False)
    date_end = fields.Datetime(
        string='End Date',
        readonly=True,
        copy=False)
    duration = fields.Integer(
        string='Duration',
        help='Class duration in minuts',
        default=45)
    teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Teacher',
        default=lambda self: self._get_teacher(),
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)]},
        track_visibility='onchange')
    training_plan_line_id = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Training Plan Line',
        domain="[('teacher_id','=',teacher_id)]",
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)]},
        required=True,
        track_visibility='onchange')
    substitution = fields.Boolean(
        string='Substitution?',
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)]})
    substitute_teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Substitute Teacher',
        states={
            'ready': [('readonly', True)],
            'ended': [('readonly', True)]},
        track_visibility='onchange')
    attendance_line_ids = fields.One2many(
        comodel_name='edu.attendance.sheet.line',
        inverse_name='attendance_sheet_id',
        string='Attendance lines',
        states={
            'ended': [('readonly', True)]})
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        compute='_compute_students',
        string='Students',
        copy=False)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('ready', 'Ready to Start'),
            ('ended', 'Ended'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
        track_visibility='onchange')
    filters = fields.Selection(
        selection=[
            ('all', 'All Students'),
            ('manual', 'Manual Selection of Students')],
        string='Filter',
        default='all',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)

    @api.model
    def _get_teacher(self):
        if not self.env.user.has_group('education.group_education_teacher'):
            return None
        return self.env.user.partner_id.id

    @api.one
    @api.depends('training_plan_line_id')
    def _compute_students(self):
        student_ids = []
        if not self.training_plan_line_id:
            return
        enrollments = self.env['edu.enrollment'].search([
            ('state', '=', 'active'),
            ('training_plan_id', '=',
                self.training_plan_line_id.training_plan_id.id),
            '|',
            ('classroom_id', '=', self.training_plan_line_id.classroom_id.id),
            ('classroom_id', '=', False)])
        student_ids = list(set([er.student_id.id for er in enrollments]))
        self.student_ids = [(6, 0, student_ids)]

    @api.one
    def to_ready_filter_all(self):
        enrollments = self.env['edu.enrollment'].search([
            ('state', '=', 'active'),
            ('training_plan_id', '=',
                self.training_plan_line_id.training_plan_id.id),
            '|',
            ('classroom_id', '=', self.training_plan_line_id.classroom_id.id),
            ('classroom_id', '=', False)])
        student_ids = list(set([er.student_id.id for er in enrollments]))
        self.attendance_line_ids = [
            (0, 0, {'student_id': e}) for e in student_ids]

    @api.one
    def to_ready(self):
        if not self.state == 'draft':
            return
        self.state = 'ready'
        self.date_start = fields.Datetime.now()
        if not hasattr(self, 'to_ready_filter_%s' % self.filters):
            return
        fnc = getattr(self, 'to_ready_filter_%s' % self.filters)
        fnc()

    @api.one
    def to_ended(self):
        if self.state != 'ready':
            return
        self.state = 'ended'
        self.date_end = fields.Datetime.now()

    @api.one
    def to_cancelled(self):
        if self.state not in ['draft', 'ready']:
            return
        self.state = 'cancelled'

    @api.one
    def to_draft(self):
        if self.state != 'cancelled':
            return
        self.state = 'draft'
        for line in self.attendance_line_ids:
            line.unlink()
