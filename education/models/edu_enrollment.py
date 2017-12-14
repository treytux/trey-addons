# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class EduEnrollment(models.Model):
    _name = 'edu.enrollment'
    _description = 'Enrollment'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        default=lambda s: s.env['ir.sequence'].get('edu.enrollment'),
        readonly=True,
        copy=False)
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
        copy=False)
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        required=True,
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
        track_visibility='onchange')
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
        track_visibility='onchange',
        domain="[('training_plan_id','=',training_plan_id)]",
        copy=False)
    student_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Student',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)]},
        track_visibility='onchange')
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_enrollment2res_partner_rel',
        column1='enrollment_id',
        column2='parnter_id',
        string='Tutors',
        domain="[('student_ids', 'in', student_id)]")
    comments = fields.Text(
        string='Comments')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('ended', 'Ended'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
        track_visibility='onchange')

    @api.one
    def to_active(self):
        if not self.state == 'draft':
            return
        if not self.classroom_id:
            raise exceptions.Warning(_('Please, select a classroom.'))
        self.state = 'active'

    @api.one
    def to_ended(self):
        if not self.state == 'active':
            return
        self.state = 'ended'

    @api.one
    def to_cancelled(self):
        if self.state not in ['draft', 'active']:
            return
        self.state = 'cancelled'

    @api.one
    def to_draft(self):
        if not self.state == 'cancelled':
            return
        self.state = 'draft'

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if not self.student_id:
            return
        self.tutor_ids = self.student_id.tutor_ids
